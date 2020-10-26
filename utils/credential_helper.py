def get_zerodha_credentails():
    import os, json

    return json.load(open("./resource/zerodha_login.json", "r"))
