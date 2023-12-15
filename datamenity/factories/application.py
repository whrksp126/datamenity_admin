from flask import Flask
from datamenity.config import SECRET_KEY, USE_ADMIN_SERVER

def create_application():
    app = Flask(__name__, template_folder='../templates')
    app.config.from_object('datamenity.config')
    
    '''
    if USE_ADMIN_SERVER:
        from datamenity.views.account import admin_account
        from datamenity.views.hotels import admin_hotels
        from datamenity.views.log import admin_log
        from datamenity.views.usergroup import admin_usergroup
        from datamenity.views.banner import admin_banner
        from datamenity.views.roomtype import admin_roomtype

        app.register_blueprint(admin_account)
        app.register_blueprint(admin_hotels)
        app.register_blueprint(admin_log)
        app.register_blueprint(admin_usergroup)
        app.register_blueprint(admin_banner)
        app.register_blueprint(admin_roomtype)

    from datamenity.views.api import admin_api
    app.register_blueprint(admin_api)
    '''
    
    return app 