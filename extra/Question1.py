from flask import Flask

app = Flask(__name__)


@app.route("/<id>")
def generateResponse(id):
    if(any(i.isdigit() for i in id)):
        result = ""
        for s in id:
            if not s.isdigit():
                result = result+s
        return "Welcome, "+result+", to my CSCB20 website!"
    else:
        if id.isupper():
            return "Welcome, "+id.lower()+", to my CSCB20 website!"
        elif id.islower():
            return "Welcome, "+id.upper()+", to my CSCB20 website!"
        else:
            return "Welcome, "+id+", to my CSCB20 website!"
