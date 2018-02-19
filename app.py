import  pickle

from flask import Flask, jsonify


app = Flask(__name__)


@app.route('/')
def hello():
    return jsonify(msg='OK')


@app.route('/log')
def show_log():
    try:
        with open('auto.log', 'r') as f:
            data = f.read().splitlines()
    except Exception as e:
        print(e)
        return jsonify(msg='暂无数据')
    return jsonify(log=data)


@app.route('/status')
def shwo_status():
    try:
        with open('status.log', 'rb') as f:
            data = pickle.load(f)
    except Exception as e:
        print(e)
        return jsonify(msg='暂无数据')
    return jsonify(status=data)


if __name__ == '__main__':
    app.run(host='0.0.0.0')
