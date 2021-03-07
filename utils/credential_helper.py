def get_zerodha_credentails():
    import json

    return json.load(open("./resource/zerodha_login.json", "r"))
