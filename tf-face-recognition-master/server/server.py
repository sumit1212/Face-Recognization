import json
from time import time
import pyttsx3
from PIL import Image
from flask import Flask, request, Response

# assuming that script is run from `server` dir
import sys, os
sys.path.append(os.path.realpath('..'))

from tensorface import detection
from tensorface.recognition import recognize, learn_from_examples

# For test examples acquisition
SAVE_DETECT_FILES = False
SAVE_TRAIN_FILES = True

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0


# for CORS
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST')  # Put any other methods you need here
    return response


@app.route('/')
def index():
    return Response(open('./static/detect.html').read(), mimetype="text/html")


@app.route('/detect', methods=['POST'])
def detect():
    try:
        #print(request.files['image'])
        image_stream = request.files['image'] # get the image
        image = Image.open(image_stream)

        # Set an image confidence threshold value to limit returned data
        threshold = request.form.get('threshold')
        if threshold is None:
            threshold = 0.5
        else:
            threshold = float(threshold)

        faces = recognize(detection.get_faces(image, threshold))
        
        print(faces)
        count = 0
        box_area = 0

        for f in faces:
            #print(f.data())
            h_w = (f.data()['h'] *f.data()['w'] )

            if h_w > box_area:
                box_area = h_w
                index_of_face = count
            print('data',h_w,f.data()['name'], index_of_face)  
            # label = f.data()['name']
            # engine = pyttsx3.init()
            # engine.say(label)
            # engine.runAndWait()
               
            count +=1 
        try:
            faces = [faces[index_of_face]]
        except:
            pass
        j = json.dumps([f.data() for f in faces])
        print("Result:", j)

        #with open('data.json', 'w') as outfile:
        #    json.dump(j, outfile)

        # save files
        if SAVE_DETECT_FILES and len(faces):
            id = time()
            with open('test_{}.json'.format(id), 'w') as f:
                f.write(j)

            image.save('test_{}.png'.format(id))
            for i, f in enumerate(faces):
                f.img.save('face_{}_{}.png'.format(id, i))

        return j

    except Exception as e:
        import traceback
        traceback.print_exc()
        print('POST /detect error: %e' % e)
        return e


@app.route('/train', methods=['POST'])
def train():
    try:
        # image with sprites
        image_stream = request.files['image']  # get the image
        image_sprite = Image.open(image_stream)

        # forms data
        name = request.form.get('name')
        num = int(request.form.get('num'))
        size = int(request.form.get('size'))

        # save for debug purposes
        if SAVE_TRAIN_FILES:
            image_sprite.save('dataset/train_{}_{}_{}.png'.format(name, size, num))

        info = learn_from_examples(name, image_sprite, num, size)
        return json.dumps([{'name': n, 'train_examples': s} for n, s in info.items()])

    except Exception as e:
        import traceback
        traceback.print_exc()
        #print('POST /image error: %e' % e)
        return e

my_dir = '/home/bigblue/Music/Test/tf-face-recognition-master/server/dataset/'

@app.route('/initTrainingSet', methods=['POST'])
def initTrainingSet():
    train_files = [f for f in os.listdir(my_dir) if f.endswith('.png')]
    print(train_files)
    for f in  train_files:
        name, size, num = f.split(".")[0].split("_")[1:]
        img = Image.open(os.path.join(my_dir, f))
        learn_from_examples(name, img, int(num), int(size))
    print("train complete!")

initTrainingSet()

if __name__ == '__main__':
    app.run(debug=False, host='127.0.0.1', ssl_context='adhoc')
    # app.run(host='0.0.0.0')
