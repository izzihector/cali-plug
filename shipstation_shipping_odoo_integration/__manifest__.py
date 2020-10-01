{
    'name': 'Shipstation Odoo Shipping Connector',
    'version': '13.0.15.11.2019',
    'author': "Vraja Technologies",
    'price': 249,
    'currency': 'EUR',
    'license': 'AGPL-3',
    'category':"Website",
    'summary':"We are providing following modules, Shipping Operations, shipping, odoo shipping integration,odoo shipping connector, dhl express, fedex, ups, gls, usps, stamps.com, shipstation, bigcommerce, easyship, amazon shipping, sendclound, ebay, shopify.",
    'depends': ['delivery','sale'],
    'data': [
	     'security/ir.model.access.csv',
             'view/shipstation_odoo_integration_config.xml',
             'view/shipstation_store_view.xml',
             'view/shipstaion_operation_detail.xml',
             'view/shipstation_delivery_carrier.xml',
             'view/shipstation_delivery_carrier_service.xml',
             'view/delivery_carrier.xml',
             'view/shipstation_delivery_carrier_package.xml',
             'view/stock_picking.xml',
             ],
    'images': [
        'static/description/odoo_shipstation.png',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}