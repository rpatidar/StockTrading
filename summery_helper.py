if __name__ == "__main__":
    from api.bot_api import api_controller
    import multiprocessing as mp
    from utils.credential_helper import get_zerodha_credentails

    api_controller(mp.Event(), get_zerodha_credentails(), mode="audit")
