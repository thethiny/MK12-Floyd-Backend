def load_secrets():
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        try:
            from yaml import safe_load as load_yaml
            import os
            with open("secrets.yaml", "r") as f:
                secrets = load_yaml(f)
                for key, value in secrets.items():
                    os.environ[key] = value
        except ImportError:
            return False
    return True