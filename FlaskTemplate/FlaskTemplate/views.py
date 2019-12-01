"""
Routes and views for the flask application.
"""

from datetime import datetime
from flask import render_template,jsonify,request
import random,re
from flask_mail import Message
from .models import User,db,Question,Answers,Block,mail
from FlaskTemplate import app, lm
from flask_login import login_user, logout_user, current_user, login_required





#ПОЛУЧИТЬ ВОПРОСЫ И ИНФУ БЛОКА
#ПОЛУЧАЮ
#{
#	"id_block":"1"
#}
#ОТПРАВЛЯЮ
#{
#  "count": 2, // количество вопросов
#  "questions": {
#    "1": { // номер вопроса
#      "answers": {
#        "answer1": "1",
#        "answer2": "2", //варианты ответов
#        "answer3": "3",
#        "answer4": "4"
#      },
#      "count_of_answers": 4, // количество ответов
#      "text": "1" // сам вопрос
#    },
#    "2": {
#      "answers": {
#        "answer1": "1_2",
#        "answer2": "2_2",
#        "answer3": "3_2",
#        "answer4": "4_2"
#      },
#      "count_of_answers": 4,
#      "text": "2"
#    }
#  }
#}

@app.route('/api/get_block_info',methods=['POST'])
def get_block_info():
    if (request.method=='POST'):
        data = request.get_json()
        try:
            id_block = data['id_block']
        except KeyError: 
            output_data = jsonify({'status':'0','desc':'ID in POST doesnt exist'})
            return output_data
        block = Block.query.filter_by(block_type=id_block).first()
        if block is not None:
            output_data = block.get_Questions()
            output_data.update({'status':'1'})
            return jsonify(output_data)
        else:
            output_data = jsonify({'status':'0','desc':'Block doesnt exist'})
            return output_data



@app.route('/api/create_question',methods=['POST'])
def create_question():
    if (request.method =='POST'):
        data = request.get_json()
        text = data['text']

        
        if Question.query.filter_by(text=text).count() > 0:
            return jsonify({"succsess":"exists, no", "text" : str(Question.query.filter_by(text=text).all())})

        q = Question(text=text)
        answers = Answers(answer1=data['ans1'], answer2=data['ans2'], answer3=data['ans3'], correct_answer=data['correct'])
        answers.correct_answer = data["correct"]
        answer4 = data.get('ans4')
        answer5 = data.get('ans5')
        answer6 = data.get('ans6')

        if answer4 is not None:
            answers.answer4 = answer4

        if answer5 is not None:
            answers.answer5 = answer5

        if answer6 is not None:
            answers.answer6 = answer6

        q.answers = answers

        block = Block.query.filter_by(block_type=data['id']).first()
        if block is None:
            block = Block(block_type=data['id'])
            db.session.add(block)

        block.questions.append(q)

        db.session.commit()
        return jsonify({"succsess":"added, yes"})


#ПОЛУЧИТЬ КОНКРЕТНЫЙ ВОПРОС?????
@app.route('/api/get_question',methods=['POST'])
def get_question():
    if(request.method=='POST'):
        data = request.get_json()
        try:
            id_question = data['id_question']
        except KeyError:
            output_data = jsonify({'status':'0','desc':'ID doesnt exist'})
            return output_data
        question = Question.query.get(id_question)
        if question is not None:
            output_data = question.get_Question()
            output_data.update(question.get_Answers())
            output_data.update({'status':'1'})
            output_data = jsonify(output_data)
        else:
            output_data = jsonify({'status':'0','desc':'Question doesnt exist'})
        return output_data

#@app.route('/login_check')
#def check_login():

#@app.route('/check')
#def check():
#   u = User(username="admin1232",email="admin123")
#   db.session.add(u)
#   db.session.commit()
#   return jsonify({'size':len(User.query.all())})





#ПРОВЕРКА ПОЛУЧЕННЫХ ОТВЕТОВ
#ПРОВЕРКА РЕЗУЛЬТАТОВ
#ПОЛУЧАЮ
#{
#	"id_block":"2", // айди блока
#	"username":"admin", // имя пользователя
#	"answers":{
#		"1":{//номер вопроса
#			"text":"1", //текст вопроса
#			"user_answer":"2" //ответ пользователя (номер ответа)
#		},
#		"2":{
#			"text":"2",
#			"user_answer":"3"
#		},
#		"count":"2" //количество вопросов для проверки
#	}
#}

#ОТПРАВЛЯЮ
#{
#  "block_id": "2", //айди блока
#  "result": {
#    "1": {
#      "status": "correct" //статус
#    },
#    "2": {
#      "correct_answer": "4_2", //правильный ответ (текст ответа)
#      "status": "mistake",
#      "user_answer": "3_2" //ответ пользователя (текст ответа)
#    }
#  }
#}

@app.route('/api/check_answers_2',methods=['POST'])
@login_required
def check_answers_2():
    data =request.get_json()
    username = current_user.username
    try:
        q_id = data['id']
        user_answer = data['answer']
    except KeyError:
        output_data = jsonify({'status':'0','desc':'ID doesnt exist'})
        return output_data
    q = Question.query.filter_by(id=int(q_id)).first()
    if q is not None:
        correct_answer = q.get_Answer_str(q.get_Correct_Answer_int())
        if (correct_answer==int(user_answer)):
            username.score+=1
            db.session.add(username)
            db.session.commit()
            status = 1
        else:
            status = 0    
        return jsonify({'correct_answer':correct_answer,'status':status})


@app.route('/api/check_answers', methods=['POST'])
@login_required
def check_answers():
    if (request.method == 'POST'):
        data = request.get_json()
        username = current_user
        b = Block.query.all()
        for block in b:
            if (block.questions.filter_by(id=int(list(data.keys())[0])).first() is not None):
                b = block
                break;
        if (len(b.users.filter_by(username=username.username).all())>0):
            output_data = {'status':'0','desc':'user has already passed the block'}
            return jsonify(output_data)
        output_data = {}
        for key in data.keys():

            user_answer = data[key]

            #current_answers = dict_of_answers[str(i)]
            #question = current_answers['text']
            #question_id = int(current_answers['id_question'])
            #user_answer = current_answers['user_answer']
            question = b.questions.filter_by(id=int(key)).first()
            bd_correct_answer = question.get_Correct_Answer_int()
            #bd_correct_answers = question.get_Answers()
            if (bd_correct_answer==int(user_answer)):
                output_data.update({key:{}})
                output_data[key].update({'is_correct':'1'})
                username.score+=1
            else:
                output_data.update({key:{'is_correct':'0','correct_answer':question.get_Answer_str(bd_correct_answer),'user_answer':question.get_Answer_str(user_answer)}})

        output_data.update({'status':'1'})
        b.users.append(username)
        username.blocks.append(b)
        db.session.add(username)
        db.session.add(b)
        db.session.commit()
        return jsonify(output_data)




#ВЫВОД ТАБЛИЦ ЛИДЕРОВ
#ПОЛУЧАЮ
#ничего get/post
#ОТПРАВЛЯЮ
#{
#  "count_of_users": 3, // количество пользователя
#  "users": {
#    "1": {
#      "score": 100, // баллы
#      "username": "admin" // имя пользователя
#    },
#    "2": {
#      "score": 80,
#      "username": "dsadsadas"
#    },
#    "3": {
#      "score": 10,
#      "username": "2312"
#    }
#  }
#}

@app.route('/api/tablescore',methods=['GET','POST'])
@login_required
def get_tablescore():
    q = User.query.order_by(User.score.desc())
    output_data = {'users':{}}
    count_of_users = 0
    for user in q.all():
        count_of_users += 1
        output_data['users'].update({count_of_users:{'score':user.score,'username':user.username}})
    output_data.update({'status':'1'})
    output_data.update({'count_of_users':count_of_users})
    return jsonify(output_data)





#ПОЛУЧИТЬ СПИСОК АКТИВНЫХ БЛОКОВ(для главного меню)
#ПОЛУЧАЮ
#{
#	"username":"test" // имя пользователя
#}
#ОТПРАВЛЯЮ
#{
#  "blocks": {
#    "1": 1, //блок активен
#    "2": 0 //блок неактивен
#  }
#}

@app.route('/api/get_active_blocks',methods=['POST'])
@login_required
def get_active_blocks():
    if request.method=='POST':
        data = request.get_json()
        username = current_user.username
        b = Block.query.all()
        output_data = {'blocks':{}}
        for block in b:
            if (block.users.filter_by(username=username).first() is not None):
                status = '1'
            else:
                status = '0'
            output_data['blocks'].update({block.id:status})
        output_data.update({'status':'1'})
        return jsonify(output_data)



#ПОЛУЧИТЬ ПОЛЬЗОВАТЕЛЬСКУЮ ИНФОРМАЦИЮ

@app.route('/api/get_user_info',methods=['POST'])
@login_required
def get_user_info():
    if request.method == 'POST':
        data = request.get_json()
        username = current_user.username

        u = User.query.filter_by(username=username).all()
        if (len(u)>0):
            u = u[0]
            output_data = {'username':u.username,'score':u.score,'email':u.email,'active_blocks':{},'is_confirmed':u.is_confirmed}
            b = Block.query.all()
            for block in b:
                if (block.users.filter_by(username=username).first() is not None):
                    output_data['active_blocks'].update({block.id:'1'})
            output_data.update({'status':'1'})
        else:
            output_data = {'status':'0','desc':'User doesnt exist'}
        return jsonify(output_data)



def send_email(app,email):
    with app.app_context():
        u = User.query.filter_by(email=email).first()
        if (u is not None):
            msg = Message('Подтверждение',recipients=[email])
            random_code = random.randint(100000,999999)
            msg.body = 'Код:'+ str(random_code)
            mail.send(msg)
            u.random_code = random_code
            db.session.add(u)
            db.session.commit()
        else:
            return None
        return random_code


@app.route('/api/check_code_email',methods=['POST'])
def check_email():
    data =request.get_json()
    try:
        email = data['email']
        code = data['code']
    except KeyError:
        output_data = {'status':'0','desc':'EMAIL doesnt exist'}
        return jsonify(output_data)
    u = User.query.filter_by(email = email).first()
    if u is not None:
        if (code==u.random_code):
            u.is_confirmed = 1
            db.session.add(u)
            db.session.commit()
            output_data = {'status':'1'}
        else:
            output_data = {'status':'0'}
        return jsonify(output_data)



@app.route('/api/send_confirmation_email',methods=['POST'])
def send_confirmation():
    data =request.get_json()
    try:
        email = data['email']
    except KeyError:
        output_data = {'status':'0','desc':'EMAIL doesnt exist'}
        return jsonify(output_data)
    send_email(app,email)
    return jsonify({'status':'1'})

#def get_Active_blocks(username):
#    b = Block.query.all()
#    output_data = {'blocks':{}}
#    for block in b:
#        if (block.users.filter_by(username=username).first() is not None):
#            status = 1
#        else:
#            status = 0
#        output_data['blocks'].update({block.id:status})
#    return output_data



#Registration
@app.route('/api/registration', methods = ['POST'])
def registration():
    regex = '^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$'
    data = request.get_json()
    try:
        username = data['login']
        email = data['email']
        password = data['password']
    except KeyError:
        return jsonify({'status':'0'})
    
    if username == "" or email == "" or password == "":
        return jsonify({'status':'0'})

    if User.query.filter_by(username=username).first() is not None or User.query.filter_by(email=email).first() is not None or re.search(regex,email) is None or username.isalnum() is False:
        return jsonify({'status':'0'})

    #if User.query.filter_by(username=username).first() is not None or User.query.filter_by(email=email).first() is not None:
        #return jsonify({'status':'0'})
    
    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify({'status':'1'})


@app.route('/api/login', methods = ['POST'])
def login():
    data = request.get_json()
    try:
        email = data['email']
        password = data['password']
    except KeyError:
        return jsonify({'status':'0','desc':'Wrong data'})
    
    user = User.query.filter_by(email=email).first() #проверка по емейлу
    if user and user.check_password(password) :
        login_user(user)
        return jsonify({'status' : 1})
    
    user = User.query.filter_by(username=email).first() #проверка по логину
    if user and user.check_password(password) :
        login_user(user)
        return jsonify({'status' : '1'})

    return jsonify({'status' : '-1','desc':'wrong username'})


@app.route('/api/logout', methods = ['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return jsonify({'status' : 1})


@app.route('/api/reset_password',methods = ['POST'])
def reset_password():
    data = request.get_json()
    try:
        email = data['email']
    except KeyError:
        output_data = {'status':0,'desc':'not found email'}
        return jsonify(output_data)
    query = User.query.filter_by(email = email).first()
    if query is not None:
        send_email(app,email)
        output_data = {'status':1}
        return jsonify(output_data)
    else:
        output_data = {'status':0,'desc':'not found email in db'}
        return jsonify(output_data)

@app.route('/api/check_code_password',methods=['POST'])
def check_code_password():
    data = request.get_json()
    try:
        code = data['code']
        email = data['email']
        password = data['password']
    except KeyError:
        output_data = {'status':0,'desc':'not found code'}
        return jsonify(output_data)
    query = User.query.filter_by(email = email).first()
    if query is not None:
        if (query.random_code == int(code)):
            query.set_password(password)
            db.session.add(query)
            db.session.commit()
            output_data = {'status':1}
        else:
            output_data = {'status':0,'desc':'incorrect_code'}
        return jsonify(output_data)
    else:
        output_data = {'status':0,'desc':'not found email in db'}
        return jsonify(output_data)


@lm.unauthorized_handler
def unauthorized():
    return jsonify({'auth' : 0,'status':'0','desc':'unauthorized'})