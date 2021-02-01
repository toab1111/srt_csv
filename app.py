import os
from werkzeug.utils import secure_filename
from flask import Flask,flash,request,redirect,send_from_directory,render_template,current_app
import re
import pandas as pd
UPLOAD_FOLDER = 'uploads/'
DOWNLOAD_FOLDER = 'download/'
#app = Flask(__name__)
app = Flask(__name__, template_folder='templates')

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DOWNLOAD_FOLDER'] = DOWNLOAD_FOLDER

ALLOWED_EXTENSIONS = {'srt'}
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def srt_to_csv(filename):
    file_path_up = UPLOAD_FOLDER + filename
    file_path_down = filename.rsplit('.', 1)[0]
    with open(file_path_up, 'r') as h:
        sub = h.readlines()

    re_pattern = r'[0-9]{2}:[0-9]{2}:[0-9]{2},[0-9]{3} -->'
    regex = re.compile(re_pattern)
    # Get start times
    start_times = list(filter(regex.search, sub))
    start_times = [time.split(' ')[0] for time in start_times]
    # Get lines
    lines = [[]]
    for sentence in sub:
        if re.match(re_pattern, sentence):
            lines[-1].pop()
            lines.append([])
        else:
            lines[-1].append(sentence)
    lines = lines[1:]         
    lon_lat = []
    j=0
    for i in lines:
        lon = float(i[1].split(',')[0][4:])
        lat = float(i[1].split(',')[1])
        lon_lat.append([start_times[j][:8],lon,lat])
        j+=1


    df = pd.DataFrame(lon_lat,columns=['time','lon','lat'])
    df.to_csv(DOWNLOAD_FOLDER+file_path_down+'.csv', index=False)  



# Upload API
@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            print('no file')
            return render_template('index.html',data='no file')
        file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            print('no filename')
            return render_template('index.html',data='no filename')

        if not allowed_file(file.filename):
            print('Wrong file type')
            return render_template('index.html',data='Wrong file type')
        else:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            print("saved file successfully")
      #send file name as parameter to downlad
            return redirect('/downloadfile/'+ filename)
    return render_template('index.html',data='Please Upload File')
# Download API
@app.route("/downloadfile/<filename>", methods = ['GET'])
def download_file(filename):
    return render_template('download.html',value=filename)
@app.route('/return-files/<filename>')
def return_files_tut(filename):
    file_load =  filename.rsplit('.', 1)[0]+'.csv'
    file_path = DOWNLOAD_FOLDER+file_load
    def generate():
        with open(file_path) as f:
            yield from f
        os.remove(UPLOAD_FOLDER+filename)
        os.remove(file_path)
    srt_to_csv(filename)
    r = current_app.response_class(generate(), mimetype='csv')
    r.headers.set('Content-Disposition', 'attachment',filename=file_load)
    return r



if __name__ == '__main__':
    app.run(debug=True)
