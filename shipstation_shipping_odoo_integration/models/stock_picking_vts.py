import os
import base64
import binascii
import logging
from PyPDF2 import PdfFileMerger
from odoo.exceptions import ValidationError
from odoo import fields,models,api,_
_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = "stock.picking"

    shipstation_order_id = fields.Char(string="Shipstation Order ID",copy=False)
    shipstation_order_key=fields.Char(string="Shipstation Order Key",copy=False)
    shipstation_shipment_id=fields.Char(string="Shipstation Order Key",copy=False)

    def update_order_in_shipstation(self):
        self.ensure_one()
        if not self.carrier_id:
            raise ValidationError("Please set proper delivery method")
        try:
            body=self.carrier_id and self.carrier_id.create_or_update_order(self)
            response_data=self.carrier_id and self.carrier_id.api_calling_function("/orders/createorder", body)
            if response_data.status_code == 200:
                responses = response_data.json()
                order_id = responses.get('orderId')
                order_key = responses.get('orderKey')
                if order_id:
                    self.shipstation_order_id = order_id
                    self.shipstation_order_key = order_key
            else:
                error_code = "%s" % (response_data.status_code)
                error_message = response_data.reason
                error_detail = {'error': error_code + " - " + error_message + " - "}
                if response_data.json():
                    error_detail = {'error': error_code + " - " + error_message + " - %s"%(response_data.json())}
                raise ValidationError(error_detail)
        except Exception as e:
            raise ValidationError(e)

    def generate_label_from_shipstation(self):
        self.ensure_one()
        if not self.carrier_id:
            raise ValidationError("Please set proper delivery method")
        final_tracking_number = []
        input_path=[]
        file_name = self.name
        pdf_merger = PdfFileMerger()
        file_name = file_name.replace('/', '_')
        file_path = "/tmp/waves/"
        directory = os.path.dirname(file_path)
        try:
            os.stat(directory)
        except:
            os.system("mkdir %s" % (file_path))
        error_detail=""
        for package_id in self.package_ids:
            try:
                if not package_id.is_generate_label_in_shipstation:
                    continue
                weight = package_id.shipping_weight
                carrier_id = package_id.carrier_id if package_id.carrier_id else self.carrier_id
                body=carrier_id.generate_label_from_shipstation(self, package_id, weight)
                response_data = carrier_id.api_calling_function("/shipments/createlabel", body)
                if response_data.status_code == 200:
                    responses = response_data.json()
                    shipment_id = responses.get('shipmentId')
                    if shipment_id:
                        self.shipstation_shipment_id=shipment_id
                        label_data = responses.get('labelData')
                        tracking_number = responses.get('trackingNumber')
                        final_tracking_number.append(tracking_number)
                        base_data = binascii.a2b_base64(str(label_data))
                        mesage_ept = (_("Shipstation Tracking Number: </b>%s") % (tracking_number))
                        message_id = self.message_post(body=mesage_ept, attachments=[('%s_Shipstation_Tracking_%s.pdf' % (self.name ,tracking_number), base_data)])
                        package_id.response_message="Sucessfully Label Generated"
                        package_id.custom_tracking_number=tracking_number
                        package_id.shipstation_shipment_id=shipment_id
                        input_path.append("%s_%s.pdf" % (file_path, tracking_number))
                        with open("%s_%s.pdf" % (file_path, tracking_number), "ab") as f:
                            f.write(base64.b64decode(message_id and message_id.attachment_ids[0] and message_id.attachment_ids[0].datas))
                else:
                    error_code = "%s" % (response_data.status_code)
                    error_message = response_data.reason
                    error_detail = {'error': error_code + " - " + error_message + " - "}
                    if response_data.json():
                        error_detail = {'error': error_code + " - " + error_message + " - %s"%(response_data.json())}
                    package_id.response_message = error_detail
            except Exception as e:
                package_id.response_message =e
        if self.weight_bulk:
            try:
                weight = self.weight_bulk
                body=self.carrier_id and self.carrier_id.generate_label_from_shipstation(self, False, weight)
                response_data=self.carrier_id and self.carrier_id.api_calling_function("/shipments/createlabel", body)
                if response_data.status_code == 200:
                    responses = response_data.json()
                    shipment_id = responses.get('shipmentId')
                    if shipment_id:
                        self.shipstation_shipment_id=shipment_id
                        label_data = responses.get('labelData')
                        tracking_number = responses.get('trackingNumber')
                        final_tracking_number.append(tracking_number)
                        base_data = binascii.a2b_base64(str(label_data))
                        mesage_ept = (_("Shipstation Tracking Number: </b>%s") % (tracking_number))
                        message_id = self.message_post(body=mesage_ept, attachments=[('%s_Shipstation_Tracking_%s.pdf' % (self.name ,tracking_number), base_data)])
                        input_path.append("%s_%s.pdf" % (file_path, tracking_number))
                        with open("%s_%s.pdf" % (file_path, tracking_number), "ab") as f:
                            f.write(base64.b64decode(message_id and message_id.attachment_ids[0] and message_id.attachment_ids[0].datas))
                else:
                    error_code = "%s" % (response_data.status_code)
                    error_message = response_data.reason
                    error_detail = {'error': error_code + " - " + error_message + " - "}
                    if response_data.json():
                        error_detail = {'error': error_code + " - " + error_message + " - %s"%(response_data.json())}
                    self.message_post(body=error_detail)

            except Exception as e:
                self.message_post(body=e)
        if not final_tracking_number:
            raise ValidationError("{}".format(error_detail))
        self.carrier_tracking_ref =','.join(final_tracking_number)

        for path in input_path:
            pdf_merger.append(path)

        with open("%s_%s.pdf" % (file_path, file_name), 'wb') as fileobj:
            pdf_merger.write(fileobj)

        with open("%s_%s.pdf" % (file_path, file_name), "rb") as f1:
            f1.seek(0)
            buffer = data = f1.read()
            f1.close()
            file_data_temp = base64.b64encode(buffer)

        att_id = self.env['ir.attachment'].create({'name':"Wave -%s"%(file_name or ""),'type':'binary', 'datas': file_data_temp or "",'mimetype':'application/pdf' , 'res_model': 'stock.picking', 'res_id':self.id, 'res_name' :self.name })

        if os.stat(directory):
            os.system("%s" % (file_path))
            os.system("rm -R %s" % (directory))

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/binary/download_document?model=ir.attachment&field=datas&id=%s&filename=%s' % (att_id.id,self.name.replace('/', '_')),
            'target': 'self'
        }
