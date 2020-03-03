from celery import Celery

app = Celery('tasks',
             backend='redis://storage:6379/0',
             brokers='pyamqp://guest@broker//',
             include='pyr_start.tasks')


@app.task
def greet_guest():
    print('Hello, Guest!')
    return 'Greet attendee'


@app.task(serializer='json')
def serial_page(page_dict):
    print("This is my page dict: ", page_dict)
    return page_dict
