from flask import render_template, request, session, flash, redirect
import random
from flask_wtf.csrf import CSRFProtect
import datetime
from flask_login import LoginManager, login_required, current_user, login_user, logout_user
import time

from app import app
from models import Meal, Category, User, Order, db, generate_password_hash
from forms import ORDER, USER, RegistrationForm


app.secret_key = 'my-super-secret-phrase-I-do-not-tell-this-to-nobody'
csrf = CSRFProtect(app)
login_manager = LoginManager(app)
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


def total():
    cart_list = []
    total_cost = 0
    cart = session.get("cart", [])
    ######getting ids from session and finding in db elemnts with ids for templates###
    for id in cart:
        newmeal = db.session.query(Meal).filter(Meal.id == id).first()
        cart_list.append(newmeal)
        total_cost += int(newmeal.price)
        session["total"] = total_cost
    return total_cost


@app.route("/", methods=["POST", "GET"])
def index():
    diction = {}
    randomlist = []
    counter = 0
    min = 10
    categories = db.session.query(Category).all()
    for category in categories:
        if len(db.session.query(Category).filter(Category.title == category.title).first().meal) < min:
            min = len(db.session.query(Category).filter(Category.title == category.title).first().meal)
        diction[category.title] = db.session.query(Category).filter(Category.title == category.title).first().meal
    while counter < 3:
        rand = random.randrange(1, min)
        if rand not in randomlist:
            randomlist.append(rand)
            counter += 1
    total_cost = total()
    return render_template("main.html", diction=diction, categories=categories, randomlist=randomlist,
                           amount=len(session.get("cart", [])), total_cost=total_cost, role=session.get("role"))


@app.route("/cart/", methods=["POST", "GET"])
def cart():
    form = ORDER()
    ######добавление элемента ##########################
    if request.method == "POST" and request.form.get('cart'):
        cart = session.get("cart", [])
        meal = request.form.get('cart')
        cart.append(meal)
        session['cart'] = cart
    ######удаление из сессии выбранного элемента########
    elif request.method == "POST" and request.form.get('delete'):
        delete = request.form.get('delete')
        cart = session.get("cart", [])
        if delete in session["cart"]:
            cart.pop(session["cart"].index(delete))
            total_cost = session.get("total")
            total_cost -= int(db.session.query(Meal).filter(Meal.id == delete).first().price)
            session["total"] = total_cost
            flash("Блюдо удалено из корзины")
        session["cart"] = cart
    #######sending order form###########################
    elif request.method == "POST" and request.form.get('submit'):
        if form.validate_on_submit():
            if form.validate_mail(form):
                flash("Пользователь должен быть зарегистрирован")
                return redirect("/registration")
            elif not session.get("total"):
                flash("Заказ не может быть пустым!")
            else:
                user = db.session.query(User).filter(User.mail == form.mail.data).first()
                now = datetime.datetime.now()
                cart_list = []
                total_cost = 0
                cart = session.get("cart", [])
                for id in cart:
                    newmeal = db.session.query(Meal).filter(Meal.id == id).first()
                    cart_list.append(newmeal)
                    total_cost += int(newmeal.price)
                    session["total"] = total_cost
                order = Order(data=now.strftime("%Y-%m-%d %H:%M"), summ=total_cost, status="выполняется",
                              user_id=user.id, user=user, meals=cart_list)
                db.session.add(order)
                db.session.commit()
                session.pop("cart")
                session.pop("total")
                return render_template("ordered.html")
    cart_list = []
    cart = session.get("cart", [])
    for id in cart:
        newmeal = db.session.query(Meal).filter(Meal.id == id).first()
        cart_list.append(newmeal)
    total_cost = total()

    if(db.session.query(User).filter(User.id == session.get("_user_id")).first() != None):
        userautofields = db.session.query(User).filter(User.id == session.get("_user_id")).first()
    else:
        userautofields = []
    return render_template("cart.html", cart=cart_list, total_cost=total_cost, form=form, amount=len(cart),
                           role=session.get("role"),
                           user=userautofields)


@app.route("/account/")
@login_required
def acc():
    user_id = session.get("_user_id")
    user = db.session.query(User).filter(User.id == user_id).first()
    orders = user.orders
    return render_template("account.html", role=session.get("role"),
                           name=db.session.query(User).filter(User.id == session.get("_user_id")).first().name,
                           amount=len(session.get("cart", [])), total_cost=total(), orders=orders)



@app.route("/login", methods=["POST", "GET"])
def login():
    if session.get("_user_id"):
        return redirect("/")
    form = USER()
    if session.get("user"):
        return redirect("/")
    if request.method == "POST":
        if form.validate_on_submit():
            user = db.session.query(User).filter(User.mail == form.mail.data).first()
            if user and user.password_valid(form.password.data):
                login_user(user)
                session["role"] = user.role
                return redirect("/")
            else:
                flash("Неправильный пароль")
        else:
            flash("Пользователь с такой почтой не зарегистрирован")
    return render_template("auth.html", form=form)


@app.route('/logout', methods=["GET", "POST"])
@login_required
def logout():
    if session.get("cart"):
        session.pop("total")
        session.pop("cart")
    session.pop("role")
    logout_user()
    return """<h2> SUCCESSFULLY LOGGEDOUT. please wait...</h2>
    <script>    
     window.setTimeout(function(){

       // 5 sec redirect (JS)
       window.location.href = "/";

       }, 3000);

 </script>"""


@app.route('/registration', methods=["GET", "POST"])
def registr():
    if session.get("_user_id"):
        return redirect("/")
    form = RegistrationForm()
    if request.method == "POST":
        if form.validate_on_submit():
            password = generate_password_hash(form.password1.data)
            user = User(name=form.name.data, mail=form.mail.data, password_hash=password, address=form.address.data)
            db.session.add(user)
            db.session.commit()
            return """<h2> SUCCESSFULLY REGISTERED. please wait...</h2>
                <script>    
                 window.setTimeout(function(){
    
                   // 3 sec redirect (JS)
                   window.location.href = "/login";
    
                   }, 3000);
    
             </script>"""
    return render_template("reg.html", form=form)



@app.after_request
def redirect_to_login(responce):
    if responce.status_code == 401:
        return redirect("/login")
    elif responce.status_code == 403:
        return redirect("/login")
    else:
        return responce


@app.errorhandler(500)
def page_not_found(error):
    return '<img src="data:image/png;base64,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uGOPPbapUPO5z32u6Exx5plnFmPPRW3geeedVwztcvXVVxdDsURP3W9/+9vFeHpVRU/caI6eOHFiOadn9Md5AgYu4+gxIAyEcfQaWXHFFdMaa6yRVltttbTgggsW+9uZKuPodSaCSQxOHOuMgYrnnXfeNMMMM5Q//aQYADmGF6n6zNriiy+edtxxx7TmmmuWcxqLYUyuuOKKIqBWrYWMgBgdJqroj/ME0BlBjwGhStCLYPLzn/+8LPWu2WabLS2xxBJlqbHuBIhll1226GAQnwbRjO4EvfXWWy/tuuuuRbirKpozY7DgKjbZZJOiN+70009fzmlOPFd42GGHFTWIjURzcDQlf/azny3ndKw/zhNAZwQ9BoQqQa8vrbTSSunEE08sS411NUDstNNOadttty3CSrO6EvSi9unII48savKaET1rv//97xc1bo1EwNtss83KUtdFDeJPf/rTdPfdd5dzOhY1bEcffXRZ6lh/nCeAznhGDzIVzaDf/e53+yw8zDTTTMWzcM2GvBBBvErI23rrrXsk5IVZZpklHXHEEZU+Ai06iMSYfr2hr88TMLAIepChjTfeuAhFfSkGS46aymbFECPXXXddWerYyiuvnIYPH16WekaEvehwUaV37mWXXVZO9Zz+OE/AwCLoQWbmmWeetPPOO5elvhEdB9Zdd92y1Jy77rqr4efWRm1XNNlON13Pv2VFL+Att9yyLHXs3nvvrVTrWFV/nCdg4BH0IDPRFBidPfpKhK+qvVLbM3r06HKqY+uss06lJtau2mKLLRoesxhm5f777y9L3dfX5wkYmAQ9yMicc85ZhKK+tPrqqxfjvHVFDLh85513lqWORS/b3hSBK3oKNxLP6vWE/jhPwMAk6EFG1l9//TTjjDOWpb6x4YYbllPNi8+UHT9+fFlqX/TkXX755ctS76nSieShhx4qp7qnP84TMDAJepCR//u//yun+kb0tI0ava567bXXyqmODR06tNOBlntKdCRp1PO1yvZW0dfnCRi4jKPHgFBlHL0ILfExWn0haqnmn3/+stRYlfHZ4lm5a665ptiPnlBlHL0VVlghnXrqqWWpeSNHjkwnnHBCWWpfDKcSHTH6wlZbbVWM6deZG264ocPauP44TwCdUaMHpajN+cxnPtMnX82EvKrikxv6OjwsvfTS5VTXjB07tpzq2JAhQ8qp3ldlXVW2uTP9cZ6AgUvQg0xU+YiuntbddTaqPQt9GfSik0QjVba5M/1xnoCBS9CDTMwxxxzlVN/p7jpjwOJGenLsukYmTJhQTnUsmt27oz/OEzBwCXqQif4Yk62765xrrrnKqY6NGzeunOp9VdY199xzl1NdY+w8oC8JepCJaTHoVQlNr7/+ejnVu6JfWqNm2ej9290aOUEP6EuCHmSiL4Ygaau766wS9Br1/O0pTz75ZMOm2yo1kI30x3kCBi5BD+g30QO50dh1L774YnrllVfKUu+55557yqmO6UgBTGsEPaDfRDPocsstV5Y69ve//72c6j1V1tGdwaEB+oOgB/SrNdZYo5zq2IgRIyr1iO2qu+++Oz3++ONlqWOCHjCtEfSAflUlPEWHjPg0id4wadKkhp+aEqKZecEFFyxLANMGQQ/oV0sssURacskly1LHLrjggvTYY4+VpZ5T9XU32GCDcgpg2iHoAf1u5513Lqc6NnHixPSTn/wkvfbaa+Wc7hs1alS67LLLylLH5p133rT55puXJYBph6AH9LtVV101rbzyymWpYxHy9t5772IolO666qqr0rHHHluWOrf99tv7fFpgmiToAVOFKrV6YcyYMWm//fZL119/ffF8XbNiUOQTTzwxnXHGGZV+f9FFF00bbrhhWQKYtgyqxXDwkLlLLrmk0gP3888/fznVt2KIkcMOO6wsfdL555+fLr300rLUvt133z1tscUWZan79t1334aDFZ911lmVnq+rqup5qltkkUXSdtttl9Zcc82GnzgR4/GNHDkyXXHFFZU/Pzc+1/aUU05JSy21VDmnc/1xngA6I+gxIDQbIPraSiutVNQydWSgBL0Qzam33HJLWapmuummSyussEIRyOLTNoYMGVI80xe1d9Hc++CDDxZBr1lHHnlkWnvttctSY4IeMLXRdAtMVQ488MC0zDLLlKVqogn2oYceSldeeWURtqIW7vTTTy8C/o033tilkDds2LCmQh7A1EjQA6YqgwcPTkcffXRaeumlyzl9b6uttiqahAGmdYIeMNWJ5teolVtvvfXKOX1jxhlnTAcffHDaddddyzkA0zZBD5gqRc3ej370ozR8+PA0aNCgcm7vmWeeedJJJ51kYGQgK4IeMFXbdttti+ftVllllXJOz4pavC233DKde+65Re9ngJwIesBUL57XO/7444sat+WXX76c2z3TTz992mijjdJFF12UdttttzTnnHOWPwHIh6AHTDOGDh2aTjvttHT22WcXTbpRjsBW1RxzzJHWXXfd4jm8GAYlBl6eb775yp8C5Mc4esA07e23305PPPFEGjt2bDFuXnwfN25c0SQ711xzFV/RuSMGw45x9mLMPYCBQtADAMiUf20BADIl6AEAZErQAwDIlKAHAJApQQ8AIFOCHgBApgQ9AIBMCXoAAJkS9AAAMiXoAQBkStADAMiUoAcAkClBDwAgU4IeAECmBD0AgEwJegAAmRL0AAAyJegBAGRK0AMAyJSgBwCQKUEPACBTgh4AQKYEPQCATAl6AACZEvQAADIl6AEAZErQAwDIlKAHAJApQQ8AIFOCHgBApgQ9AIBMCXoAAJkS9AAAMiXoAQBkStADAMiUoAcAkClBDwAgU4IeAECmBD0AgEwJegAAmRL0AAAyJegBAGRK0AMAyJSgBwCQKUEPACBTgh4AQKYEPQCATAl6AACZEvQAADIl6AEAZErQAwDIlKAHAJApQQ8AIFOCHkylHn300TR+/Piy1H1PPPFEGjduXFma8vV7el0dqbKevtqWqdFrr72WnnrqqbI0dZk0aVJ66623ylLfGcjXA/QEQY/KTj755HTGGWeUpclefvnlNHz48OImEJ588sm0zz77FNN1tVotbb/99ulvf/tbOWfa8+tf/zqdc845ZalvnHTSScXx7Cm/+tWv0iOPPFKWpnz9nl5XuPnmm9OFF15Yliarsp7e2JZpxR133PGJYza1+N///jfF33Z757c3NHM99NU2wbRE0KOyjTbaKP31r39NEydOLOektMACC6TZZ5893X333UX5pptuSmuuuWYxXffQQw+ld955J6211lrlHKYG++23X1pyySXLUs97/fXX03//+9+yVF1vbxddM3jw4PT5z3++LHX9/Darmeuhr7YJpiWCHpUts8wyaf7550+33XZbOWeyb33rW+lPf/pTEQCj1u7rX/96+ZPJbrzxxmLejDPOWM5harDiiiumOeaYoyxNPabW7Rro5pprrvTDH/6wLPUd1wN0z/Q/aVFOQ0PRDHvLLbek9ddfv5yT0iKLLJLOPPPM4s14woQJRc1f3dtvv100+e6///5pzjnnLOdObuKNJploCv7zn/+cxo4dW7yhTzfdlP97VFnusMMOSyussEIRMk8//fR07rnnFk2USy+99BTrjGbmX/ziF+mCCy5If/zjH9MDDzyQllpqqTRkyJByiY5FjWWs84tf/GI5p309uV/XXHNNWm211Ypa07pYdsSIEUWt6auvvtrU/kTgjhqZRRddtCjHcVtwwQXTpz71qYbriu2qb3Mc3xtuuKE4nkOHDk3TTz99+Rsfi+az2KZnn322eJ133323WHd9PWPGjElnnXVWOu2009Kdd96ZvvCFLxQ1w6H1djV7zqpeC9EMefbZZxc/v+SSS4ptiFqjeeaZp1xisjjvJ554YrGt8ToRdmLbL7/88rT66quXS318Pqscm7popj3hhBOK3/n3v/9d/BMV18GLL76YvvrVr5ZLNX9NdbQNjY5lHLvllluueJbz+OOPL/6mb7311uJ4zj333MUydR2d3/Z0tl1xPfzlL38pronWYl9jufjnsur10Mw2wYDScuOGyt56663aJptsUnvllVfKOZO1vJHXWgJe7bbbbivnTHbdddfVDjjggLI0Wcubc23TTTetXXHFFbWWm2btscceq7UEwdpBBx1UmzRpUrlU9eWGDx9ea3nzr7WEhtpLL71Ue/7552stN4ra5ptvXnvuuefKpWq1XXbZpdZyUymmP/zww1rLzb3WEkKLciMtN71aSzAoS+3rjf267777ylKt1hJeajvttFOt5UZflJvdn7322qt2++23l6UpX7/RuuJn3/ve92qjR48u1jV+/PjieMRrfvDBB8Uyrb3zzju1iy66qHbUUUcVr9Fy0y3mx3paQlLt0EMPrbUEp9r9999f22OPPYp9r2u9Lc3uY/xulWuhJbwV+/j+++8X1/Tvf//7Yplx48aVS9SKa3njjTeuXXvttbWWYFhs78EHH1zs9xFHHFEu1fyxCS0Bqvh7ufrqqz967Tgmsd2tX7vqtVJlGxodyzh2LWGptu+++xbrffzxx4v17LnnnuUSH+vo/LbVaLvi+O+6667FuagbNWpUMS9+FqpeD1W3CQYaQY+mxY003lBbu/TSS2vrr79+7amnnirnTBZv6DfffHNZmvzmHG/cLf/Jl3MmmzhxYm2HHXao3XTTTUW56nIhlmvv5h83zcMPP7yYfv3114sbZlc1Cnq9tV/1G9w///nP4oZZD9hd2Z84F1WCXtt1xQ152LBhtXvuuacot3bMMcfUrrzyyrI0pREjRtSOO+64sjRZrGfvvff+6CYeYr0bbLBBcaMO9W3pyj7G7za6Fjqy4447fnReYp+33377Kc5HmDBhQhFC6mGsK8cmzvV2221Xu+GGG8o5k7333ntTvHbVa6XKNlQ5lrGuH/zgB1MEpAiX8XcdYbit9s5va1WPzTPPPFPbZpttiust1hfTMa+umeuh0TbBQDRl3T9UEE2z8Uxey/VTzklFed111y2+17W8WRcPRq+99trlnFQ0q0SzWevm3TDDDDOkLbbYomgqClWXq1tnnXXKqY9tu+22afTo0aklVBTNgtHUddlll/XKUA29tV+h5SZXNH397Gc/K5r3Qm/tT3vrim2OZrBVVlmlKLf2zW9+8xPPbDYS+9n6ec1oVg0tN/Lie11X97HRtVA3adKkoinwueeeSy0hq2g+rD/IH/NinS0BtCjXRYeEeCa1rivHJn4nHmn4xje+Uc6ZbKaZZvrEa1e9phptQ9VjufXWW6eZZ565LKU033zzFdv1xhtvlHOqq3psFltsseL8RDN2fMV0zGurt/+GIVeCHk2L53hmnXXWIhSE6FUb5T333LN4Nmpi2Sv3pptu+kQnjBdeeCEtvPDCxRt2W5/5zGeKG2youlxde8tFUIkb80svvVRsw6mnnlqEzx122CHtu+++6YorrihuRD2ht/brX//6VzrllFOKm/ubb75Zzk29sj8drSu2OW6sO+200ye+Yhuef/75cslq4jm31uLaiWesWoew0NV9bHQthPiHJIb8Oe2004rnxI477rj0j3/846NrN5ZbaKGF2n2tOD51XTk28QxeR9dA29euek012oaqx7Lts3hhlllm+cS5qaKZY7PZZpsVPfNjnL5NN920nDul3v4bhlx98h0EKohahni4P8T3TTbZpLiBx0PiccP84IMPiqFY2tZGxI2ko9qBqNGJGoRQdbnORC1NfNWDRdwcDznkkKKDwc4775wefvjh4mbx4YcfFj/vjt7arwghxxxzTNGZJWo7Yn/qenp/OlpXPAQfHW2ic0Pbr+ik8Jvf/KZYrjf01D62vhais0Fse4S8CHh77bVXOuqoo9J6661XLp2KThkxeHEjXTk28dpRU9dI1Wul6jb05vXfnmaOTfyzGKEwgl5sV0f6eh8gB4IeXRK9bu+5556i6Su+R7Nt2HjjjYueddGjMJpfokaitejZGM1WMdp9WxEMozdeqLpcXX0cv9aid3D0Im1bgxS9/aI33pFHHlnccKOGpbt6a79iDLG4uX3pS18qevyeffbZ5U8+1lP709G6Fl988aI3ddRyRe1b66+oTYmmvd7WzD42uhai5vLLX/5ymnfeecufThb7WFff5wcffLCc87EIinVdOTZLLLFEETrvv//+cs7H/vOf/5RT1a+VZrehN67/9lTdrgh40cv34IMPLkJc/JMR8zrTV/sAORD06JLZZputGHYjRuf5yle+8tFzPTFMRtSExJAVbWvzQjQDRZNZvLHHMzwh/huP/+7jJhfPCIWqy9XFEA7XX3/9R88NPvDAA8VwDvEaIZqZY0iG1k1QcROPprr6s2ixfFf11n7F8nW77bZbEaojyFTZn7bitZ5++uliOp5Pa6ujdcW5jea2GNZizJgx5RKTA08018eNtj3R1BbNi1G7W6V2rK2u7GNodC1EAImaoNbN01ELHc/w1QNG7POwYcOK0BFDn4R4vWuvvbZ4/bquHJsIOrEt8Tv10BjnI147roH6dlW9VqpsQ1ePZWcand+qxyaGr4nnFSO4Lb/88sVzijGvrSr70N42defvGnIwqOXN6+Mn6qEJMa5YNJvER4PFzbMumlXigen4ijfe9kSt30UXXVT8PJprll122WIw1rY3nSrLRRNONL9FTU3csKO5K24GcZOph82oQYntiWcIo+ksbgQRVr/zne+kVVddtVgmHnCPcbjaEx+BFj8bNGhQOWdKEWxjm3pjvyI810VAOfbYY4tmxwgzne1PW7FsPIMXtSHR2SI6XdRfv7N1Rc1eNMGNHDkyXXrppcX66jfb+J16Z4q2orY39ik+Xzdqz2Jctii3XU/YaqutilAV11F9W+KYNDpnbVW5FkKcrwhW9dq1eL2VV145HX744cVzX3XxWMJvf/vbIuTFPkTnjHhm7s477yyae+uaPTYh1n/xxRcX10CEoviH6Wtf+1raY4890u9+97vimIeq11Rn21Dl+m/vGgitz01r7Z3f+ja31tl2XXXVVcV5itevP4sYoTdq9qLWNZ7da+Z6aG+b4nm+jv6uYSAQ9OhXY8eOLXrTxU2sM50t1/YGFc8vxY2gI3ETiGajuLn2lp7Yr6qa2Z+o/QjdWV+EpwiL7d3U24qbdjxkH/vYHVX3sZlrIY5F1J61bsKN7W2v80M0NdZrPCOcxXlr+5nOoZljUxfbGM/j1f+J6Ggbql4rjbahJ6//Zs5vV45NRzrbh5665iAXmm7pV3GDqxI6qi4XOgt5IXp49mbIC72xXx1pZn9iXd1dXzznVvVmHYGlJ264XT1nnV0LcRxah7xQD1jRRBrNh/Xmv3rIi5qxqFFqb8iQ0MyxqYttbF1T3F7IC1WvlUbb0JPXfzPntyvHpiOd7UNPXXOQC0EPoI2oeYpnUKMZ8Lzzzis6c0TzXzxbFs2ErceGBJiaabplmjdq1KhiWJe2tTMMPD19LUSzajzvF50fohYpnuNr+6wawNRM0AMAyJSmWwCATAl6AACZEvQAADIl6AEAZErQAwDIlKAHAJApQQ8AIFOCHgBApgQ9AIBMCXoAAJkS9AAAMiXoAQBkStADAMiUoAcAkClBDwAgU4IeAECmBD0AgEwJegAAmRL0AAAyJegBAGRK0AMAyJSgBwCQKUEPACBTgh4AQKYEPQCATAl6AACZEvQAADIl6AEAZErQAwDIlKAHAJApQQ8AIFOCHgBApgQ9AIBMCXoAAJkS9AAAMiXoAQBkStADAMiUoAcAkClBDwAgU4IeAECmBD0AgEwJegAAmRL0AAAyJegBAGRK0AMAyJSgBwCQKUEPACBTgh4AQKYEPQCATAl6AACZEvQAADIl6AEAZErQAwDIlKAHAJApQQ8AIFOCHgBApgQ9AIBMCXoAAJkS9AAAMiXoAQBkStADAMiUoAcAkClBDwAgU4IeAECmBD0AgEwJegAAmRL0AAAyJegBAGRK0AMAyJSgBwCQKUEPACBTgh4AQKYEPQCATAl6AACZEvQAADIl6AEAZErQAwDIlKAHAJApQQ8AIFOCHgBApgQ9AIBMCXoAAJkS9AAAMiXoAQBkStADAMiUoAcAkClBDwAgU4IeAECmBD0AgEwJegAAmRL0AAAyJegBAGRK0AMAyJSgBwCQKUEPACBTgh4AQKYEPQCATAl6AACZEvQAADIl6AEAZErQAwDIlKAHAJApQQ8AIFOCHgBApgQ9AIBMCXoAAJkS9AAAMiXoAQBkStADAMiUoAcAkClBDwAgU4IeAECmBD0AgEwJegAAmRL0AAAyJegBAGRK0AMAyJSgBwCQKUEPACBTgh4AQKYEPQCATAl6AACZEvQAADIl6AEAZErQAwDIlKAHAJApQQ8AIFOCHgBApgQ9AIBMCXoAAJkS9AAAMiXoAQBkStADAMiUoAcAkClBDwAgU4IeAECmBD0AgEwJegAAmRL0AAAyJegBAGRK0AMAyJSgBwCQKUEPACBTgh4AQKYEPQCATAl6AACZEvQAADIl6AEAZErQAwDIlKAHAJApQQ8AIFOCHgBApgQ9AIBMCXoAAJkS9AAAspTS/wNvB0aBQ1zIOgAAAABJRU5ErkJggg==" align="center" class="w-75" alt="">'


@app.errorhandler(404)
def page_not_found404(error):
    return '<img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAnoAAAGKCAYAAACb0OyIAAAABGdBTUEAALGOfPtRkwAAACBjSFJNAACHDgAAjBIAAPxoAACFkgAAeeQAAO3tAAA7IgAAIN+/WeXLAAAKqGlDQ1BJQ0MgUHJvZmlsZQAASMetl2dQFOkWhk/35EQaGAEJQ06C5Cg5DqAgGUwMM4QhjOPAkEyoLCq4oqiIgAldJCi4BkDWgIhiWhQT5gVZVNTrYkBUVG4Dl+Huj/1xq+6pOtVPnf76/U73nK/qHQD6Za5IlIrKAaQJM8Qhvh7sqOgYNukpEEEDlMAO9Lm8dJF7cHAg/GN8ugfI+PW26bgW/G8hz49P5wEgwRjH8dN5aRifwLKBJxJnAOD4WF0nK0M0zhswVhRjDWJcOc6Jk3x0nOMmuWNiTViIJ8b3Ach0LlecCED7E6uzM3mJmA4dj7G5kC8QYmyNsQsviYvtQ8fuway0tKXjvA9jw7j/0kn8m2acVJPLTZTy5LtMBNlLkC5K5ebA/zvSUiVTe2hhSU8S+4VgVwXsm1WmLA2QsjBuXtAUC/gT6yc4SeIXPsW8dM+YKeZzvQKmWJIS7j7FXPH0s4IMTtgUi5eGSPWFqfMCpfrxHCnHp3uHTnGCwIczxblJYZFTnCmImDfF6SmhAdNrPKV1sSRE2nOC2Ef6jmnp073xuNN7ZSSF+UnfK97LW9qPMFy6RpThIdURpQZP95zqK62nZ4ZKn83AhmqKk7n+wdM6wdJvAp4gACHEQxpwgQ1+4AWQEZ89PlfguVSUIxYkJmWw3bFTEs/mCHlms9iW5hbYBI6fucmf9MP9ibOEsMjTtdwUALfLAKj3dC0Sm926WgCW2nRN9xs2+sUArdd4EnHmZG181IEAVJAFRVDBzrQOGIIpWIItOIEbeIM/BEEYRMNi4EES1rcYsmAFrIECKIItsAPKYS8cgBo4AsegGU7DebgE1+Am3IVH0AsD8BqG4BOMIghCQhgIE1FBNBE9xASxROwRF8QbCURCkGgkFklEhIgEWYGsQ4qQEqQc2Y/UIr8ip5DzyBWkG3mA9CGDyHvkK4pD6agiqo7qo7NRe9QdDUDD0EVoIroMzUXz0c1oGVqFHkab0PPoNfQu2ou+RodxgKPhWDgtnCnOHueJC8LF4BJwYtwqXCGuFFeFa8C14jpxt3G9uDe4L3ginoln403xTng/fDieh1+GX4XfhC/H1+Cb8B342/g+/BD+B4FBUCOYEBwJHEIUIZGQRSgglBKqCScJFwl3CQOET0QikUU0INoR/YjRxGTicuIm4m5iI7GN2E3sJw6TSCQVkgnJmRRE4pIySAWkXaTDpHOkW6QB0mcyjaxJtiT7kGPIQvJacim5jnyWfIv8gjxKkaPoURwpQRQ+JYdSTDlIaaXcoAxQRqnyVAOqMzWMmkxdQy2jNlAvUh9TP9BoNG2aA20+TUDLo5XRjtIu0/poX+gKdGO6J30hXULfTD9Eb6M/oH9gMBj6DDdGDCODsZlRy7jAeMr4LMOUMZPhyPBlVstUyDTJ3JJ5K0uR1ZN1l10smytbKntc9obsGzmKnL6cpxxXbpVchdwpuR65YXmmvIV8kHya/Cb5Ovkr8i8VSAr6Ct4KfIV8hQMKFxT6mTimDtOTyWOuYx5kXmQOKBIVDRQ5ismKRYpHFLsUh5QUlKyVIpSylSqUzij1snAsfRaHlcoqZh1j3WN9naE+w31G/IyNMxpm3JoxojxT2U05XrlQuVH5rvJXFbaKt0qKylaVZpUnqnhVY9X5qlmqe1Qvqr6ZqTjTaSZvZuHMYzMfqqFqxmohasvVDqhdVxtW11D3VRep71K/oP5Gg6XhppGssV3jrMagJlPTRVOguV3znOYrthLbnZ3KLmN3sIe01LT8tCRa+7W6tEa1DbTDtddqN2o/0aHq2Osk6GzXadcZ0tXUnau7Qrde96EeRc9eL0lvp16n3oi+gX6k/nr9Zv2XBsoGHINcg3qDx4YMQ1fDZYZVhneMiEb2RilGu41uGqPGNsZJxhXGN0xQE1sTgcluk+5ZhFkOs4Szqmb1mNJN3U0zTetN+8xYZoFma82azd7O1p0dM3vr7M7ZP8xtzFPND5o/slCw8LdYa9Fq8d7S2JJnWWF5x4ph5WO12qrF6p21iXW89R7r+zZMm7k2623abb7b2tmKbRtsB+107WLtKu167BXtg+032V92IDh4OKx2OO3wxdHWMcPxmONfTqZOKU51Ti/nGMyJn3NwTr+ztjPXeb9zrwvbJdZln0uvq5Yr17XK9ZmbjhvfrdrthbuRe7L7Yfe3HuYeYo+THiOejp4rPdu8cF6+XoVeXd4K3uHe5d5PfbR9En3qfYZ8bXyX+7b5EfwC/Lb69XDUOTxOLWfI385/pX9HAD0gNKA84FmgcaA4sHUuOtd/7ra5j+fpzRPOaw6CIE7QtqAnwQbBy4J/m0+cHzy/Yv7zEIuQFSGdoczQJaF1oZ/CPMKKwx6FG4ZLwtsjZCMWRtRGjER6RZZE9kbNjloZdS1aNVoQ3RJDiomIqY4ZXuC9YMeCgYU2CwsW3ltksCh70ZXFqotTF59ZIruEu+R4LCE2MrYu9hs3iFvFHY7jxFXGDfE8eTt5r/lu/O38wXjn+JL4FwnOCSUJLxOdE7clDia5JpUmvRF4CsoF75L9kvcmj6QEpRxKGUuNTG1MI6fFpp0SKghThB1LNZZmL+0WmYgKRL3LHJftWDYkDhBXpyPpi9JbMhQxc3NdYij5SdKX6ZJZkfk5KyLreLZ8tjD7eo5xzsacF7k+ub8sxy/nLW9fobVizYq+le4r969CVsWtal+tszp/9UCeb17NGuqalDW/rzVfW7L247rIda356vl5+f0/+f5UXyBTIC7oWe+0fu8G/AbBhq6NVht3bfxRyC+8WmReVFr0bRNv09WfLX4u+3lsc8LmrmLb4j1biFuEW+5tdd1aUyJfklvSv23utqbt7O2F2z/uWLLjSql16d6d1J2Snb1lgWUtu3R3bdn1rTyp/G6FR0VjpVrlxsqR3fzdt/a47WnYq763aO/XfYJ99/f77m+q0q8qPUA8kHng+cGIg52/2P9SW61aXVT9/ZDwUG9NSE1HrV1tbZ1aXXE9Wi+pHzy88PDNI15HWhpMG/Y3shqLjsJRydFXv8b+eu9YwLH24/bHG07onag8yTxZ2IQ05TQNNSc197ZEt3Sf8j/V3urUevI3s98OndY6XXFG6UzxWerZ/LNj53LPDbeJ2t6cTzzf376k/dGFqAt3OuZ3dF0MuHj5ks+lC53unecuO18+fcXxyqmr9lebr9lea7puc/3k7za/n+yy7Wq6YXej5abDzdbuOd1nb7neOn/b6/alO5w71+7Ou9t9L/ze/Z6FPb33+fdfPkh98O5h5sPRR3mPCY8Ln8g9KX2q9rTqD6M/Gntte8/0efVdfxb67FE/r//1n+l/fhvIf854XvpC80XtS8uXpwd9Bm++WvBq4LXo9eibgn/J/6vyreHbE3+5/XV9KGpo4J343dj7TR9UPhz6aP2xfTh4+OmntE+jI4WfVT7XfLH/0vk18uuL0axvpG9l342+t/4I+PF4LG1sTMQVcyesAA5LNCEB4P0hAEY0APMmAFVm0hNPBDLp4ycI/oknffNE2AIcaMO8CJb+WFbmAehhycRuBbsBhLkBamUlzf9EeoKV5aQWrRmzJqVjYx8wL0gyAvjeMzY22jw29r0aa/YhQNunSS8+HkTsH0qJFoqYMS9kj+T93RED/BtQMACLL7YRYgAAAAlwSFlzAAAOxAAADsQBlSsOGwAAH31JREFUeF7t3QeUHVX9B/AbSuiEJlJFinSDIFIE/yCCooAUaR4UAqFIR9pBaSIIglQFpB2QoiAR6UWjYFCQ0Js0pReBCCGEFgJ5//1N5sFm2d03b2ty9/M5Z8/OnZ19U/fNd++de9+gWosEAEB2piu/AwCQGUEPACBTgh4AQKYEPQCATAl6AACZEvQAADIl6AEAZErQAwDIlKAHAJApQQ8AIFOCHgBApgQ9AIBMCXoAAJkS9AAAMiXoAQBkStADAMiUoAcAkClBDwAgU4IeAECmBD0AgEwJegAAmRL0AAAyJegBAGRK0AMAyJSgBwCQKUEPACBTgh4AQKYEPQCATAl6AACZEvQAADIl6AEAZErQAwDIlKAHAJApQQ8AIFOCHgBApgQ9AIBMCXoAAJkS9AAAMiXoAQBkStADAMiUoAcAkClBDwAgU4IeAECmBD0AgEwJegAAmRL0AAAyJegBAGRK0AMAyJSgBwCQKUEPACBTgh4AQKYEPQCATAl6AACZEvQAADIl6AEAZErQAwDIlKAHAJApQQ8AIFOCHgBApgQ9AIBMCXoAAJkS9AAAMiXoAQBkStADAMiUoAcAkClBDwAgU4IeAECmBD0AgEwJegAAmRL0AAAyJegBAGRK0AMAyJSgBwCQKUEPACBTgh4AQKYEPQCATAl6AACZEvQAADIl6AEAZErQAwDIlKAHAJApQQ8AIFOCHgBApgQ9AIBMCXoAAJkS9AAAMiXoAQBkStADAMiUoAcAkClBDwAgU4IeAECmBD0AgEwJegAAmRL0AAAyJegBAGRK0AMAyJSgBwCQKUEPACBTgh4AQKYEPQCATAl6AACZEvQAADIl6AEAZErQAwDIlKAHAJApQQ8AIFOCHgBApgQ9AIBMCXoAAJkaVGtRTkO2RowYkS677LKyNHVZaqml0vHHH1+WAKDnCHoMCJdcckm68MILy9LUZemll05nnHFGWQKAnqPpFgAgU4IeAECmBD0AgEwJegAAmRL0AAAyJegBAGRK0INWZppppj7/Gjx4cLl2AOhZxtFjQKgyjt7MM8+crr322rIEANM+NXoAAJkS9AAAMiXowQA2bty4NGHChLLUN8aMGVNO9bxJkyalN954Iz3zzDPpxRdfTG+//Xb5k2lbf5wnIA+e0WNAmNaf0Rs9enS69957y1L71lprrTR06NCy1L6nn3463XTTTcX3CENjx44tPmc3Pm+3rSuvvDK9/PLLZal9W221VZpvvvnKUvti22+//fZinc8++2wRxnriOL/77rvpvvvuS3feeWd65JFHin158803i9dvbcYZZ0xzzTVX+vSnP51WWWWVtOqqq6ZlllkmTTddz/+f2x/nCaAzgh4DwrQe9M4///x06aWXlqX27b777mmLLbYoS1OKgHXRRRelW2+9tZzzsV/+8pdpueWWK0sf23fffYsA1ZmzzjorLbnkkmVpSnfddVdxzB9//PFyzmQRvG644Yay1Jx4u4p9iPP08MMPpw8//LD8SXPmnHPOtPrqq6dtttkmLbbYYuXc7uuP8wTQGU23kLH33nsvnXDCCWmXXXZpNzyEnv5fL5pM99lnn/TjH//4EyEvdHV9UXMXIemYY45JDzzwQJdDXoiav5EjRxbHJY5Po5rL3tYf5wkYGAQ9yFQ09x1wwAFFoOksJLRt6uyORx99tAh58b0jza7v1VdfTfvvv3869NBD05NPPlnO7RlxXOL4DBs2LJ177rk9eiyq6o/zBAwcgh5k6Lnnnkt77713euKJJ8o5HeupmqLbbrstHXjggUVtWWeaWV80z+65557poYceKuf0jqgdvPzyy9MhhxySxo8fX87tff1xnoCBRdCDzLzwwgvF83WvvPJKOadzPVFTNGrUqHTUUUel999/v5zTsaqB5cYbb0wHHXRQ0Yu2r0Tnjr322qt4Vq639cd5AgYeQQ8yEjVTxx13XHrrrbfKOY11N0BE0+opp5zSVI1To3X+4Q9/SCeffHL64IMPyjl956WXXioCWPR27S39cZ6AgUnQg4xcfPHFlZoBW+tOk2CEj+OPP77p8eo6W+cdd9yRzjnnnLLUnEGDBqUhQ4YUPWkXWmihNOuss5Y/aU7sz+GHH16MX9cb+vo8AQOXoAeZiKFQGg3t0VoMJ7PAAgukwYMHl3OaN2LEiPTggw+WpcZmn332tPDCC3cYWmLcuGOPPbapUPO5z32u6Exx5plnFmPPRW3geeedVwztcvXVVxdDsURP3W9/+9vFeHpVRU/caI6eOHFiOadn9Md5AgYu4+gxIAyEcfQaWXHFFdMaa6yRVltttbTgggsW+9uZKuPodSaCSQxOHOuMgYrnnXfeNMMMM5Q//aQYADmGF6n6zNriiy+edtxxx7TmmmuWcxqLYUyuuOKKIqBWrYWMgBgdJqroj/ME0BlBjwGhStCLYPLzn/+8LPWu2WabLS2xxBJlqbHuBIhll1226GAQnwbRjO4EvfXWWy/tuuuuRbirKpozY7DgKjbZZJOiN+70009fzmlOPFd42GGHFTWIjURzcDQlf/azny3ndKw/zhNAZwQ9BoQqQa8vrbTSSunEE08sS411NUDstNNOadttty3CSrO6EvSi9unII48savKaET1rv//97xc1bo1EwNtss83KUtdFDeJPf/rTdPfdd5dzOhY1bEcffXRZ6lh/nCeAznhGDzIVzaDf/e53+yw8zDTTTMWzcM2GvBBBvErI23rrrXsk5IVZZpklHXHEEZU+Ai06iMSYfr2hr88TMLAIepChjTfeuAhFfSkGS46aymbFECPXXXddWerYyiuvnIYPH16WekaEvehwUaV37mWXXVZO9Zz+OE/AwCLoQWbmmWeetPPOO5elvhEdB9Zdd92y1Jy77rqr4efWRm1XNNlON13Pv2VFL+Att9yyLHXs3nvvrVTrWFV/nCdg4BH0IDPRFBidPfpKhK+qvVLbM3r06HKqY+uss06lJtau2mKLLRoesxhm5f777y9L3dfX5wkYmAQ9yMicc85ZhKK+tPrqqxfjvHVFDLh85513lqWORS/b3hSBK3oKNxLP6vWE/jhPwMAk6EFG1l9//TTjjDOWpb6x4YYbllPNi8+UHT9+fFlqX/TkXX755ctS76nSieShhx4qp7qnP84TMDAJepCR//u//yun+kb0tI0ava567bXXyqmODR06tNOBlntKdCRp1PO1yvZW0dfnCRi4jKPHgFBlHL0ILfExWn0haqnmn3/+stRYlfHZ4lm5a665ptiPnlBlHL0VVlghnXrqqWWpeSNHjkwnnHBCWWpfDKcSHTH6wlZbbVWM6deZG264ocPauP44TwCdUaMHpajN+cxnPtMnX82EvKrikxv6OjwsvfTS5VTXjB07tpzq2JAhQ8qp3ldlXVW2uTP9cZ6AgUvQg0xU+YiuntbddTaqPQt9GfSik0QjVba5M/1xnoCBS9CDTMwxxxzlVN/p7jpjwOJGenLsukYmTJhQTnUsmt27oz/OEzBwCXqQif4Yk62765xrrrnKqY6NGzeunOp9VdY199xzl1NdY+w8oC8JepCJaTHoVQlNr7/+ejnVu6JfWqNm2ej9290aOUEP6EuCHmSiL4Ygaau766wS9Br1/O0pTz75ZMOm2yo1kI30x3kCBi5BD+g30QO50dh1L774YnrllVfKUu+55557yqmO6UgBTGsEPaDfRDPocsstV5Y69ve//72c6j1V1tGdwaEB+oOgB/SrNdZYo5zq2IgRIyr1iO2qu+++Oz3++ONlqWOCHjCtEfSAflUlPEWHjPg0id4wadKkhp+aEqKZecEFFyxLANMGQQ/oV0sssURacskly1LHLrjggvTYY4+VpZ5T9XU32GCDcgpg2iHoAf1u5513Lqc6NnHixPSTn/wkvfbaa+Wc7hs1alS67LLLylLH5p133rT55puXJYBph6AH9LtVV101rbzyymWpYxHy9t5772IolO666qqr0rHHHluWOrf99tv7fFpgmiToAVOFKrV6YcyYMWm//fZL119/ffF8XbNiUOQTTzwxnXHGGZV+f9FFF00bbrhhWQKYtgyqxXDwkLlLLrmk0gP3888/fznVt2KIkcMOO6wsfdL555+fLr300rLUvt133z1tscUWZan79t1334aDFZ911lmVnq+rqup5qltkkUXSdtttl9Zcc82GnzgR4/GNHDkyXXHFFZU/Pzc+1/aUU05JSy21VDmnc/1xngA6I+gxIDQbIPraSiutVNQydWSgBL0Qzam33HJLWapmuummSyussEIRyOLTNoYMGVI80xe1d9Hc++CDDxZBr1lHHnlkWnvttctSY4IeMLXRdAtMVQ488MC0zDLLlKVqogn2oYceSldeeWURtqIW7vTTTy8C/o033tilkDds2LCmQh7A1EjQA6YqgwcPTkcffXRaeumlyzl9b6uttiqahAGmdYIeMNWJ5teolVtvvfXKOX1jxhlnTAcffHDaddddyzkA0zZBD5gqRc3ej370ozR8+PA0aNCgcm7vmWeeedJJJ51kYGQgK4IeMFXbdttti+ftVllllXJOz4pavC233DKde+65Re9ngJwIesBUL57XO/7444sat+WXX76c2z3TTz992mijjdJFF12UdttttzTnnHOWPwHIh6AHTDOGDh2aTjvttHT22WcXTbpRjsBW1RxzzJHWXXfd4jm8GAYlBl6eb775yp8C5Mc4esA07e23305PPPFEGjt2bDFuXnwfN25c0SQ711xzFV/RuSMGw45x9mLMPYCBQtADAMiUf20BADIl6AEAZErQAwDIlKAHAJApQQ8AIFOCHgBApgQ9AIBMCXoAAJkS9AAAMiXoAQBkStADAMiUoAcAkClBDwAgU4IeAECmBD0AgEwJegAAmRL0AAAyJegBAGRK0AMAyJSgBwCQKUEPACBTgh4AQKYEPQCATAl6AACZEvQAADIl6AEAZErQAwDIlKAHAJApQQ8AIFOCHgBApgQ9AIBMCXoAAJkS9AAAMiXoAQBkStADAMiUoAcAkClBDwAgU4IeAECmBD0AgEwJegAAmRL0AAAyJegBAGRK0AMAyJSgBwCQKUEPACBTgh4AQKYEPQCATAl6AACZEvQAADIl6AEAZErQAwDIlKAHAJApQQ8AIFOCHkylHn300TR+/Piy1H1PPPFEGjduXFma8vV7el0dqbKevtqWqdFrr72WnnrqqbI0dZk0aVJ66623ylLfGcjXA/QEQY/KTj755HTGGWeUpclefvnlNHz48OImEJ588sm0zz77FNN1tVotbb/99ulvf/tbOWfa8+tf/zqdc845ZalvnHTSScXx7Cm/+tWv0iOPPFKWpnz9nl5XuPnmm9OFF15Yliarsp7e2JZpxR133PGJYza1+N///jfF33Z757c3NHM99NU2wbRE0KOyjTbaKP31r39NEydOLOektMACC6TZZ5893X333UX5pptuSmuuuWYxXffQQw+ld955J6211lrlHKYG++23X1pyySXLUs97/fXX03//+9+yVF1vbxddM3jw4PT5z3++LHX9/Darmeuhr7YJpiWCHpUts8wyaf7550+33XZbOWeyb33rW+lPf/pTEQCj1u7rX/96+ZPJbrzxxmLejDPOWM5harDiiiumOeaYoyxNPabW7Rro5pprrvTDH/6wLPUd1wN0z/Q/aVFOQ0PRDHvLLbek9ddfv5yT0iKLLJLOPPPM4s14woQJRc1f3dtvv100+e6///5pzjnnLOdObuKNJploCv7zn/+cxo4dW7yhTzfdlP97VFnusMMOSyussEIRMk8//fR07rnnFk2USy+99BTrjGbmX/ziF+mCCy5If/zjH9MDDzyQllpqqTRkyJByiY5FjWWs84tf/GI5p309uV/XXHNNWm211Ypa07pYdsSIEUWt6auvvtrU/kTgjhqZRRddtCjHcVtwwQXTpz71qYbriu2qb3Mc3xtuuKE4nkOHDk3TTz99+Rsfi+az2KZnn322eJ133323WHd9PWPGjElnnXVWOu2009Kdd96ZvvCFLxQ1w6H1djV7zqpeC9EMefbZZxc/v+SSS4ptiFqjeeaZp1xisjjvJ554YrGt8ToRdmLbL7/88rT66quXS318Pqscm7popj3hhBOK3/n3v/9d/BMV18GLL76YvvrVr5ZLNX9NdbQNjY5lHLvllluueJbz+OOPL/6mb7311uJ4zj333MUydR2d3/Z0tl1xPfzlL38pronWYl9jufjnsur10Mw2wYDScuOGyt56663aJptsUnvllVfKOZO1vJHXWgJe7bbbbivnTHbdddfVDjjggLI0Wcubc23TTTetXXHFFbWWm2btscceq7UEwdpBBx1UmzRpUrlU9eWGDx9ea3nzr7WEhtpLL71Ue/7552stN4ra5ptvXnvuuefKpWq1XXbZpdZyUymmP/zww1rLzb3WEkKLciMtN71aSzAoS+3rjf267777ylKt1hJeajvttFOt5UZflJvdn7322qt2++23l6UpX7/RuuJn3/ve92qjR48u1jV+/PjieMRrfvDBB8Uyrb3zzju1iy66qHbUUUcVr9Fy0y3mx3paQlLt0EMPrbUEp9r9999f22OPPYp9r2u9Lc3uY/xulWuhJbwV+/j+++8X1/Tvf//7Yplx48aVS9SKa3njjTeuXXvttbWWYFhs78EHH1zs9xFHHFEu1fyxCS0Bqvh7ufrqqz967Tgmsd2tX7vqtVJlGxodyzh2LWGptu+++xbrffzxx4v17LnnnuUSH+vo/LbVaLvi+O+6667FuagbNWpUMS9+FqpeD1W3CQYaQY+mxY003lBbu/TSS2vrr79+7amnnirnTBZv6DfffHNZmvzmHG/cLf/Jl3MmmzhxYm2HHXao3XTTTUW56nIhlmvv5h83zcMPP7yYfv3114sbZlc1Cnq9tV/1G9w///nP4oZZD9hd2Z84F1WCXtt1xQ152LBhtXvuuacot3bMMcfUrrzyyrI0pREjRtSOO+64sjRZrGfvvff+6CYeYr0bbLBBcaMO9W3pyj7G7za6Fjqy4447fnReYp+33377Kc5HmDBhQhFC6mGsK8cmzvV2221Xu+GGG8o5k7333ntTvHbVa6XKNlQ5lrGuH/zgB1MEpAiX8XcdYbit9s5va1WPzTPPPFPbZpttiust1hfTMa+umeuh0TbBQDRl3T9UEE2z8Uxey/VTzklFed111y2+17W8WRcPRq+99trlnFQ0q0SzWevm3TDDDDOkLbbYomgqClWXq1tnnXXKqY9tu+22afTo0aklVBTNgtHUddlll/XKUA29tV+h5SZXNH397Gc/K5r3Qm/tT3vrim2OZrBVVlmlKLf2zW9+8xPPbDYS+9n6ec1oVg0tN/Lie11X97HRtVA3adKkoinwueeeSy0hq2g+rD/IH/NinS0BtCjXRYeEeCa1rivHJn4nHmn4xje+Uc6ZbKaZZvrEa1e9phptQ9VjufXWW6eZZ565LKU033zzFdv1xhtvlHOqq3psFltsseL8RDN2fMV0zGurt/+GIVeCHk2L53hmnXXWIhSE6FUb5T333LN4Nmpi2Sv3pptu+kQnjBdeeCEtvPDCxRt2W5/5zGeKG2youlxde8tFUIkb80svvVRsw6mnnlqEzx122CHtu+++6YorrihuRD2ht/brX//6VzrllFOKm/ubb75Zzk29sj8drSu2OW6sO+200ye+Yhuef/75cslq4jm31uLaiWesWoew0NV9bHQthPiHJIb8Oe2004rnxI477rj0j3/846NrN5ZbaKGF2n2tOD51XTk28QxeR9dA29euek012oaqx7Lts3hhlllm+cS5qaKZY7PZZpsVPfNjnL5NN920nDul3v4bhlx98h0EKohahni4P8T3TTbZpLiBx0PiccP84IMPiqFY2tZGxI2ko9qBqNGJGoRQdbnORC1NfNWDRdwcDznkkKKDwc4775wefvjh4mbx4YcfFj/vjt7arwghxxxzTNGZJWo7Yn/qenp/OlpXPAQfHW2ic0Pbr+ik8Jvf/KZYrjf01D62vhais0Fse4S8CHh77bVXOuqoo9J6661XLp2KThkxeHEjXTk28dpRU9dI1Wul6jb05vXfnmaOTfyzGKEwgl5sV0f6eh8gB4IeXRK9bu+5556i6Su+R7Nt2HjjjYueddGjMJpfokaitejZGM1WMdp9WxEMozdeqLpcXX0c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" align="center" class="w-75" alt="">'

