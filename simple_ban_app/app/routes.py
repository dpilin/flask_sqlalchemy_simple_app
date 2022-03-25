from app import simple_ban_app, db
from app.models import BlockList
from flask import Response, request, current_app
from json import dumps
from datetime import datetime
from email.mime.text import MIMEText
from sqlalchemy.exc import OperationalError

def response(code, data):
    """
    Custom JSON response
    :param code: int
    :param data: dict
    """
    return Response(
        status = code,
        mimetype = "application/json",
        response = data
    )

def send_email_with_banned_ip(ip, timestamp, app):
    """
    :param ip: str
    :param timestamp: datetime object
    :app: Flask object
    """
    app.logger.debug("Preparing an email with banned IP")
    msg = MIMEText(f"The next IP address was banned at {timestamp}: {ip}")
    msg["Subject"] = "New IP was banned"
    msg["From"] = "simple_ban_app@python"
    msg["To"] = "test@domain.com"
    app.logger.debug(f"Email was formed, here is its content:\n\n{msg.as_string()}")

    app.config["SMTP_CLIENT"].sendmail("simple_ban_app@python", "test@domain.com", msg.as_string()) 


@simple_ban_app.route("/", methods=["GET"])
def calculate_num_square():
    """
    Calculate the number's square
    """
    if BlockList.query.filter_by(ip=request.remote_addr).all():
        return response(403, dumps({"result": "Access from your IP address is forbidden"}))

    arguments = request.args.to_dict()

    current_app.logger.info(f"Received an incoming request to {str(request.url_rule)}. The request args are next: {arguments}")
    current_app.logger.debug(f"The requestor's IP is {request.remote_addr}. The path is {str(request.url_rule)}")

    if not arguments or len(arguments) > 1 or 'n' not in arguments.keys():
        return response(400, dumps({"result": "Bad argument list was provided for the request. The endpoint accepts only n = X argument where X is integer"}))

    try:
        number = int(arguments["n"])
        current_app.logger.debug(f"The provided number is {number}")
    except ValueError:
        current_app.logger.debug(f"The value of n is not an integer ({arguments['n']})")
        return response(400, dumps({"result": "The value of n is not an integer"}))
    
    number_square = number**2
    current_app.logger.debug(f"Returning the square of provided number - {number_square}")

    return response(200, dumps({"result": number_square}))

@simple_ban_app.route("/blacklisted", methods=["GET"])
def ban_visitor_of_the_page():
    """
    Check if the visitor's IP address is banned. Banning him for the first time if not
    """
    visitor_ip = request.remote_addr
    current_app.logger.info(f"Received an incoming request to {str(request.url_rule)}")
    current_app.logger.debug(f"The visitor's ip is {visitor_ip}")
    if BlockList.query.filter_by(ip=request.remote_addr).all():
        return response(403, dumps({"result": f"Access from your IP address ({visitor_ip}) is forbidden"}))
    else:
        record = BlockList(ip=visitor_ip, path=str(request.url_rule), timestamp=datetime.now())
        current_app.logger.debug(f"The next record will be added to the blocklist table: {record}")
        db.session.add(record)
        db.session.commit()
        current_app.logger.debug("The record was successfully saved in the database")
        send_email_with_banned_ip(record.ip, record.timestamp, current_app)
        return response(444, dumps({"result": f"From now on your IP address ({visitor_ip}) is banned"}))

@simple_ban_app.route("/healthcheck", methods=["GET"])
def healthcheck():
    """
    A technical endpoint for the service's health checking
    """
    is_automated_check = True if request.headers.get("requestor") == "automated_healthcheck" else False
    if not is_automated_check and BlockList.query.filter_by(ip=request.remote_addr).all():
        return response(403, dumps({"result": "Access from your IP address is forbidden"}))

    current_app.logger.debug(f"Received an incoming request to {str(request.url_rule)}")
    try:
        records_qty = len(BlockList.query.all())
        return response(200, dumps({"result": f"{records_qty} record(s) is (are) in the DB at the moment"}))
    except OperationalError:
        return response(500, dumps({"result": "Internal Server Error"}))

