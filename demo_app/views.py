from django.shortcuts import render, redirect
from django.db import connection
from .forms import InputForm, SignUpForm
from .models import Customers
from sklearn.externals import joblib
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate

import numpy as np
import pandas as pd
import json

#loaded_model = joblib.load('/home/Naritoshi/naritoshi.pythonanywhere.com/demo_app/demo_model.pkl')
loaded_model = joblib.load('demo_app/demo_model.pkl')

print("[Trained Model] loaded.")

# Create your views here.

@login_required
def index(request):
    return render(request, 'demo_app/index.html', {})

@login_required
def input_form(request):
    if request.method == 'POST':
        form = InputForm(request.POST)
        if form.is_valid():
            form.save()#入力した値を保存
            return redirect('result')
        else:
            return redirect(form.errors)
    else:
        form = InputForm()
        return render(request, 'demo_app/input_form.html', {'form':form})

@login_required
def result(request):
    customers = Customers.objects.order_by('id').reverse().values_list\
    ('limit_balance', 'sex', 'education', 'marriage', 'age', 'pay_0', 'pay_2','pay_3',\
     'pay_4', 'pay_5', 'pay_6', 'bill_amt_1', 'pay_amt_1', 'pay_amt_2','pay_amt_3', 'pay_amt_4', 'pay_amt_5', 'pay_amt_6')

    x = np.array([customers[0]])
    print(x)

    y = loaded_model.predict(x)[0]
    y_proba = loaded_model.predict_proba(x)[0][y]
    y_proba = round(y_proba * 100, 2)
    result = (y, y_proba)
    print(result)

    print(connection.queries[-1]['sql'])

    if y == 0:
        if y_proba >= 75:
            comment = '貸しても返ってこない'
        else:
            comment = '貸しても返ってこないかも'
    else:
        if y_proba >= 75:
            comment = '貸していい'
        else:
            comment = '貸してもいい'
    
    #推論結果の保存
    customer = Customers.objects.order_by('id').reverse()[0]
    customer.result = y
    customer.proba = y_proba
    customer.comment = comment
    customer.save()

    return  render(request, 'demo_app/result.html', {'y':y, 'y_proba': y_proba, 'comment':comment})

@login_required
def info(request):
    # male = Customers.objects.filter(sex=1).count()
    # female = Customers.objects.filter(sex=2).count()
    # print(male)
    # print(female)
    # DBからデータの読み込み
    customers = Customers.objects.values_list(\
    'sex', 'education', 'marriage', 'age', 'result', 'proba')

    # データをDataFarame型に変換
    lis, cols = [], ['sex', 'education', 'marriage', 'age', 'result', 'proba']
    for customer in customers:
        lis.append(customer)
    df = pd.DataFrame(lis, columns=cols)

    # データの整形
    df['sex'].replace({1:"男性", 2:"女性"}, inplace=True)
    df['education'].replace({1:'graduate_school', 2:'university', 3:'high school', 4:'other'}, inplace=True)
    df['marriage'].replace({1:'married', 2:'single', 3:'others'}, inplace=True)
    df['result'].replace({0:'審査落ち', 1:'審査通過', 2:'その他'}, inplace=True)
    df['age'] = pd.cut(df['age'], [0,10,20,30,40,50,60,100], labels=['10歳未満','10代', '20代','30代','40代','50代','60代以上'])
    df['proba'] = pd.cut(df['proba'], [0,75,100], labels=['要審査', '信頼度高'])

    # データのユニークな値とその数の取得
    dic_val, dic_index = {}, {}
    for col in cols:
        _val = df[col].value_counts().tolist()
        _index = df[col].value_counts().index.tolist()
        dic_val[col] = _val
        dic_index[col] = _index

    # データをJson形式に変換
    val, index = json.dumps(dic_val), json.dumps(dic_index)
    return render(request, 'demo_app/info.html', {'val':val, 'index':index})

@login_required
def history(request):
    if request.method == 'POST':
        d_id = request.POST
        d_customer = Customers.objects.filter(id=d_id['d_id'])
        d_customer.delete()

    customers = Customers.objects.all()
    return render(request, 'demo_app/history.html', {'customers':customers})

@login_required
def calicurate(request):
    calc_result = ''
    if request.method == 'POST':
        nums = request.POST
        num1 = nums['num1']
        num2 = nums['num2']
        if (num1.isdigit() and num2.isdigit()):
            calc_result = int(num1) + int(num2)
        
    return  render(request, 'demo_app/calicurate.html', {'answer':calc_result})

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('/')
        else:
            print(form.error_messages)
            return render(request, 'demo_app/signup.html', {'form':form})
    else:
        form = SignUpForm()
        return render(request, 'demo_app/signup.html', {'form':form})