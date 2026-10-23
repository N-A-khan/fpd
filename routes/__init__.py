from routes import admin, api, auth, home, user


def register_routes(app):
    home.register(app)
    auth.register_routes(app)
    user.register_routes(app)
    admin.register_routes(app)
    api.register(app)
