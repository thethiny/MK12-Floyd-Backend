import os 

def load_secrets():
    try:
        from dotenv import load_dotenv
        if os.path.isfile(".env"):
            print("Loading secrets from .env")
            failed = load_dotenv(dotenv_path=".env")
        else:
            failed = True
    except ImportError:
        failed = True
    if failed:
        print("Loading secrets from YAML")
        try:
            from yaml import safe_load as load_yaml
            with open("secrets.yaml", "r") as f:
                secrets = load_yaml(f)
                for key, value in secrets.items():
                    os.environ[key] = str(value)
                return secrets
        except ImportError:
            return False
