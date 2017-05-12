import logging
import json
import sys
import socket, re, os, sys, inspect
from flask import Flask, render_template, redirect, url_for
from flask import request as request_flask
from flask import session as session_flask
from flask_ask import Ask, request, session, question, statement, dialog
import rest_requests as rest
from splitwise import Splitwise
import datetime
import copy, random
import requests
app = Flask(__name__)
ask = Ask(app, "/")
app.secret_key = "test_secret_key"
logging.getLogger('flask_ask').setLevel(logging.DEBUG)

token = "e2e960794d44"
account_no = "4444777755551369"
customer_id = "33336369"
consumer_key = '9avqAwEDHj08BTSWo4rbklFSH9kBkDGYJVIcLuok'
consumer_secret = 'nn93bOnzbVnTHodCep94BOOEEe4CO6vdkJKPbAZp'

questions = [["Who's your favourite actor?","brad Pitt"],
             ["How old were you when you first went out of India?", '16']
]
payee_details = {
                'sam' : '4444777755551370',
                'nick' : '4444777755551371',
                'john' : '4444777755551372',
                }
vpa_details = {
                'sam' : 'sam@icicibank',
                'nick' : 'nick@icicibank',
                'john' : 'john@icicibank',
                }
@ask.launch
def launch():
    speech_text = render_template('welcome')
    return question(speech_text).reprompt(speech_text).simple_card('GringottsResponse', speech_text)

@ask.intent('BalanceIntent')
def getAccountBalance():
    response = rest.getAccountBalance(token, account_no)
    if (response[0] == 200):
        print response[1][1]
        speech_text = render_template('balance_response', balance=response[1][1]['balance'])
    else:
        speech_text = render_template('icici_error')
    return statement(speech_text).simple_card('GringottsResponse', speech_text)

@ask.intent('RecentTransactionsIntent',
            mapping={'fromDay':'FROM_DAY', 'toDay' : 'TO_DAY'}, default={'toDay': datetime.datetime.now().strftime ("%Y-%m-%d")  })
def getRecentTransactions(fromDay, toDay):
    session.attributes['root'] = 'transactions'
    if fromDay is not None:
        speech_text = render_template('recent_transactions_response', fromDay=fromDay, toDay=toDay)
        return statement(speech_text).simple_card('GringottsResponse', speech_text)
    else:
        print "Question"
        reprompt_text = render_template('recent_transactions_reprompt')
        speech_text = render_template('recent_transactions_range_error')
        return question(speech_text).reprompt(reprompt_text)

@ask.intent('SplitwiseBalanceIntent')
def splitwiseBalance():
    if 'access_token' in session_flask:
        print session_flask['access_token']
        response = rest.getSplitWiseBalance(session_flask['access_token'])
        print response
        speech_text = render_template('splitwise_balance_response', owe=response['owe'], owed=response['owed'])
        return question(speech_text)
    else:
        speech_text = render_template('splitwise_login_response')
        url = "http://" + socket.gethostbyname(socket.gethostname()) + ":5000/splitwise"
        return statement(speech_text).standard_card(title="splitwise login", text=speech_text + " " + url)

@ask.intent('SplitwiseMaxOweIntent')
def splitwiseMaxOwe():
    speech_text = render_template('splitwise_max_owe_response')
    return question(speech_text)

@ask.intent('MoneySpentIntent',
            mapping={'recent_duration' : 'RECENT_DURATION'})

def getMoneySpent(recent_duration):
    if recent_duration is not None:
        duration = re.search('\d+', recent_duration).group(0)
        response = rest.getnDaysTransaction(token, account_no, duration)
        print "getting data for days " + duration
        if (response[0] == 200):
            print response[1]
            if (response[1][0]["message"] == "No Data Found"):
                amount = 0
            else:
                amount = response[1][0]['message']
            speech_text = render_template('money_spent_response', amount=amount, duration=duration)
        else:
            speech_text = render_template('icici_error')
        return statement(speech_text).simple_card('GringottsResponse', speech_text)
    else :
        return dialog().dialog_directive()

@ask.intent('AuthorizeIntent', mapping={})
def CheckAuth():
    ques_copy = copy.deepcopy(questions)
    q1 = ques_copy[0]
    print "question : " + q1[0]

    session.attributes['authorized'] = 0
    speech_text = render_template('ask_q1', q1 = q1[0])
    session.attributes['current_question'] = q1[0]
    session.attributes['current_answer'] = q1[1]
    session.attributes['question_number'] = 1
    return question(speech_text).simple_card('GringottsResponse', speech_text)


@ask.intent('VerifyAuthQOne',mapping={'answer':'ANSWER_Q_ONE'})
def AnswerOne(answer):
    print 'answer' + answer
    print 'stored_asnwer' + session.attributes['current_answer']
    if (answer == session.attributes['current_answer']):
        print "Correct Answer"
        speech_text = render_template('auth_verified')
        session.attributes['authorized'] = 1
        return statement(speech_text).simple_card('GringottsResponse', speech_text)
    else :
        speech_text = render_template('auth_error')
        return statement(speech_text).simple_card('GringottsResponse', speech_text)

@ask.intent('VerifyAuthQTwo', mapping={'answer':'ANSWER_Q_TWO'})
def AnswerTwo(answer):
    print 'answer' + answer
    print 'stored_asnwer' + session.attributes['current_answer']
    if (answer == session.attributes['current_answer']):
        print "Correct Answer"
        speech_text = render_template('auth_verified')
        session.attributes['authorized'] = 1
        return statement(speech_text).simple_card('GringottsResponse', speech_text)
    else :
        speech_text = render_template('auth_error')
        return statement(speech_text).simple_card('GringottsResponse', speech_text)


@ask.intent('VerifyAuthQThree',mapping={'answer':'ANSWER_Q_THREE'})
def AnswerThree(answer):
    print 'answer' + answer
    print 'stored_asnwer' + session.attributes['current_answer']
    if (answer == session.attributes['current_answer']):
        print "Correct Answer"
        speech_text = render_template('auth_verified')
        session.attributes['authorized'] = 1
        return statement(speech_text).simple_card('GringottsResponse', speech_text)
    else :
        speech_text = render_template('auth_error')
        return statement(speech_text).simple_card('GringottsResponse', speech_text)

#TODO: Add intents for name and amount
@ask.intent('TransferIntent', mapping={'payeeName':'PAYEE_NAME', 'payeeAmount' : 'PAYEE_AMOUNT'})
def transferMoney(recentDays, payeeName, payeeAmount):
    if payeeName is not None and payeeAmount is not None:
            print "payeeName - %s payeeAmount - %s" % (payeeName, payeeAmount)
            response = rest.upiFundTransferVtoV(token, customer_id, "soumyadeep@icicibank", vpa_details.get(payeeName.lower()), payeeAmount, "remarks")
            if (response[0] == 200):
                print response[1]
                try:
                    if (response[1][1]["status"] == "SUCCESS"):
                        speech_text = render_template('transfer_response', payeeName=payeeName, payeeAmount=payeeAmount)
                    else:
                        speech_text = render_template('transfer_error')
                except (KeyError, IndexError):
                    speech_text = render_template('transfer_error')
            return statement(speech_text).simple_card('GringottsResponse', speech_text)
    else :
        return dialog().dialog_directive()

#TODO: Add payee details
@ask.intent('AddPayeeIntent',
            mapping={'payeeName': 'PAYEE_NAME', 'payeeVPA' : 'PAYEE_VPA'})
def addPayee(payeeName, payeeVPA):
    if payeeName is not None and payeeVPA is not None:
        payeeName = payeeName.lower();
        payeeVPA = payeeVPA.lower();
        print "payee name %s payeeVPA %s" % (payeeName, payeeVPA)
        if payee_details.get(payeeName):
            response = rest.createVPA(token, payee_details.get(payeeName), payeeVPA.replace(" at ", "@"))
            if (response[0] == 200):
                print response[1]
                try:
                    if (response[1][1]["response"].find("mapped successfully")) :
                        speech_text = render_template('add_payee_response', payeeName=payeeName, payeeVPA=payeeVPA)
                    else:
                        speech_text = render_template('add_payee_api_error')
                except (KeyError, IndexError):
                    speech_text = render_template('add_payee_api_error')
        else:
            speech_text = render_template('add_payee_name_error')
        return statement(speech_text).simple_card('GringottsResponse', speech_text)
    else :
        return dialog().dialog_directive()

#TODO: Ask amount as response
@ask.intent('PayBillIntent',
            mapping={'billName': 'BILL_NAME'})
def payBill(billName):
    if billName is not None:
        print "billName " + billName
        speech_text = render_template('pay_bill_response', billName=billName, billAmount=678)
        return question(speech_text).simple_card('GringottsResponse', speech_text)
    else :
        speech_text = render_template('pay_bill_name_error')
        return question(speech_text).simple_card('GringottsResponse', speech_text)

#TODO: Does not exist
@ask.intent('CheckBillIntent',
            mapping={'billName': 'BILL_NAME', 'billDate': 'BILL_DATE'})
def checkBill(billName, billDate):
    if billName is not None:
        if billDate is not None:
            print "billName " + billName + "billDate " + billDate
            speech_text = render_template('check_bill_response', billName=billName, billAmount=100, billDate=billDate)
            return statement(speech_text).simple_card('GringottsResponse', speech_text)
        else:
            print "billName " + billName + "billDate " + "this month"
            speech_text = render_template('check_bill_response', billName=billName, billAmount=100, billDate="this month")
            return statement(speech_text).simple_card('GringottsResponse', speech_text)
    else :
        speech_text = render_template('check_bill_name_error')
        return question(speech_text).simple_card('GringottsResponse', speech_text)

#TODO: Add biller details
@ask.intent('AddBillerIntent',
            mapping={'billName': 'BILL_NAME', 'billerName': 'BILLER_NAME'})
def checkBill(billName, billerName):
    if billName is not None:
        if billerName is not None:
            print "billName " + billName + "billerName " + billerName
            speech_text = render_template('add_biller_response', billName=billName, billerName=billerName)
            return statement(speech_text).simple_card('GringottsResponse', speech_text)
        else:
            print "billName " + billName
            speech_text = render_template('add_biller_name_error')
            return question(speech_text).simple_card('GringottsResponse', speech_text)
    else :
        speech_text = render_template('add_biller_bill_error')
        return question(speech_text).simple_card('GringottsResponse', speech_text)

@ask.session_ended
def session_ended():
    return "", 200


@ask.intent('AMAZON.HelpIntent')
def help():
    help_text = render_template('help')
    help_reprompt = render_template('help_reprompt')
    return question(help_text).reprompt(help_reprompt)


@ask.intent('AMAZON.StopIntent')
def stop():
    bye_text = render_template('bye')
    return statement(bye_text)


@ask.intent('AMAZON.CancelIntent')
def cancel():
    bye_text = render_template('bye')
    return statement(bye_text)

@app.route("/splitwise")
def home():
    if 'access_token' in session_flask:
        return redirect(url_for("loggedin"))
    return render_template("home.html")

@app.route("/splitwise/login")
def login():

    sObj = Splitwise(consumer_key,consumer_secret)
    url, secret = sObj.getAuthorizeURL()
    session_flask['secret'] = secret
    return redirect(url)


@app.route("/splitwise/login/authorized")
def authorize():

    if 'secret' not in session_flask:
       return redirect(url_for("home"))

    oauth_token    = request_flask.args.get('oauth_token')
    oauth_verifier = request_flask.args.get('oauth_verifier')

    sObj = Splitwise(consumer_key,consumer_secret)
    access_token = sObj.getAccessToken(oauth_token,session_flask['secret'],oauth_verifier)
    session_flask['access_token'] = access_token

    return redirect(url_for("loggedin"))


@app.route("/splitwise/loggedin")
def loggedin():
    if 'access_token' not in session_flask:
       return redirect(url_for("home"))

    print rest.getMaxFriendOwed(session_flask['access_token'])
    print rest.getSplitWiseBalance(session_flask['access_token'])
    return render_template("loggedin.html")

@app.route('/splitwise/logout')
def logout():
    session_flask.pop('access_token', None)
    return redirect(url_for('home'))

@app.route('/avsauth')
def avsauth():
    access_token    = request_flask.args.get('access_token')
    refresh_token = request_flask.args.get('refresh_token')
    code = request_flask.args.get('code')
    print "access_token %s refresh_token %s code %s" % (access_token, refresh_token, code)

    data = {
        'grant_type':'authorization_code',
        'code':code,
        'client_id':'amzn1.application-oa2-client.eec9ebc38e7d4a9eb06c653bd474cd1b',
        'client_secret':'99910b388d24d4c6d5ae6f1a0255733c71354d5cde62dc6c67b38517a5bd25bb',
        'redirect_uri':'https://776c2c44.ngrok.io/avsauth'
    }

    # sending post request and saving response as response object
    r = requests.post(url = 'https://api.amazon.com/auth/o2/token', data = data)

    # extracting response text
    r = r.json()
    access_token = r['access_token']
    refresh_token = r['refresh_token']
    print "access_token %s refresh_token %s code %s" % (access_token, refresh_token, code)
    return render_template("home.html")

if __name__ == '__main__':
    #print rest.getAccountSummary(token, 33336369, account_no)
    #print rest.listPayee(token, 33336369)
    #print rest.createVPA(token, account_no, "soumyadeep@icicibank")
    app.run(threaded=True,debug=True)
