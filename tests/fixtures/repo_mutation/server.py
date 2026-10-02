MAX_UPLOAD_SIZE = 10 * 1024 * 1024

def validate_upload(size):
    if size > MAX_UPLOAD_SIZE:
        raise ValueError("too large")
