import kiteconnect
from kiteconnect import KiteConnect
import datetime, os

# Execute the command


def prerequisite_multiprocess(api_key, api_secret, clean_credential=False):
    mock_file = "./tmp/mock"
    mock = open(mock_file, "r").read() if os.path.exists(mock_file) else "0"
    if mock == "1":
        return

    session_file = "./tmp/session_file"
    return ""
    def _save_session(token):
        import json

        session = {"lastSessionDate": repr(datetime.datetime.now()), "token": token}
        filehandler = open(session_file, "w")
        json.dump(session, filehandler)
        filehandler.close()

    def _load_token():
        import json

        if not os.path.exists(session_file):
            return None
        session_data = json.load(open(session_file, "r"))
        session_data["lastSessionDate"] = eval(session_data["lastSessionDate"])
        if (
            session_data["lastSessionDate"] + datetime.timedelta(days=1)
            > datetime.datetime.now()
        ):
            return session_data["token"]
        return None

    kite = KiteConnect(api_key, api_secret)
    token = _load_token()
    if not token or clean_credential:
        print(
            "Open this link in browser to login",
            kite.login_url(),
        )
        url = input("Enter Your token URL here")
        data = kite.generate_session(
            url.split("request_token=")[1].split("&action")[0],
            api_secret=api_secret,
        )
        token = data["access_token"]
        _save_session(token)
    return token
