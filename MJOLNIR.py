from pytube import YouTube
from PyQt5.QtCore import pyqtSlot, QRect
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QApplication
from PyQt5 import uic, QtCore
import sys
import urllib
import os
from PyQt5.QtCore import QThread
from PyQt5.QtGui import QPixmap, QMovie, QImage
from PyQt5.QtGui import QIcon
import pyttsx3

cwd = os.path.dirname(os.path.realpath(__file__))


class Mjolnir(QThread):
    mjlonirSignal = QtCore.pyqtSignal(str, bytes)
    mjlonirException = QtCore.pyqtSignal(str)

    def __init__(self):
        super(Mjolnir, self).__init__()
        self.youtubeURL = ''
        self.youtubeTitle = ''
        self.youtubeThumbnail = ''

    @pyqtSlot(str, bytes)
    def run(self):
        try:
            self.youtubeTitle = self.getYoutubeTitle(self.youtubeURL)
            self.youtubeThumbnail = self.getYoutubeThumbnail(self.youtubeURL)
            self.mjlonirSignal.emit(self.youtubeTitle, self.youtubeThumbnail)
        except Exception as e:
            print(e)
            self.mjlonirException.emit(str(sys.exc_info()[1]))

    def getYoutubeThumbnail(self, url):
        youtube = YouTube(url)
        tempURL = 'https://i.ytimg.com/vi/'+youtube.video_id+'/default.jpg'
        return urllib.request.urlopen(tempURL).read()

    def getYoutubeTitle(self, url):
        youtube = YouTube(url)
        return youtube.title


class MjolnirDownload(QThread):
    mjlonirDownloadSignal = QtCore.pyqtSignal(float)
    mjlonirDownloadException = QtCore.pyqtSignal(str)
    filesize = 0

    def __init__(self):
        super(MjolnirDownload, self).__init__()
        self.youtubeURL = ""
        self.youtubeSavePath = ""
        self.youtubeQuality = ""

    @pyqtSlot(str)
    def run(self):
        self.downloadYoutube(self.youtubeURL, self.youtubeSavePath,
                             self.youtubeQuality)

    def downloadYoutube(self, url, path, quality):
        youtube = YouTube(url)
        youtube.register_on_progress_callback(self.progressDownload)
        try:
            if quality == "Best Available":
                stream = youtube.streams.filter(progressive=True,
                                                file_extension="mp4").first()
                self.filesize = stream.filesize
                stream.download(self.youtubeSavePath)
            elif quality == "1080-Video-Only":
                itag = 137
                stream = youtube.streams.get_by_itag(itag)
                self.filesize = stream.filesize
                stream.download(self.youtubeSavePath)
            elif quality == "720p-Video-Only":
                itag = 136
                stream = youtube.streams.get_by_itag(itag)
                self.filesize = stream.filesize
                stream.download(self.youtubeSavePath)
            elif quality == "480p-Video-Only":
                itag = 135
                stream = youtube.streams.get_by_itag(itag)
                self.filesize = stream.filesize
                stream.download(self.youtubeSavePath)
            elif quality == "360p-Dual":
                itag = 134
                stream = youtube.streams.get_by_itag(itag)
                self.filesize = stream.filesize
                stream.download(self.youtubeSavePath)
            elif quality == "Audio-Only-50kbps":
                itag = 249
                stream = youtube.streams.get_by_itag(itag)
                self.filesize = stream.filesize
                stream.download(self.youtubeSavePath)
            elif quality == "Audio-Only-Best":
                stream = youtube.streams.filter(type="audio").first()
        except Exception as e:
            print(e)
            self.mjlonirDownloadException.emit(str(sys.exc_info()[1]))

    def progressDownload(self, chunk, file_handle, bytes_remaining):
        remaining = (100 * bytes_remaining) / self.filesize
        step = 100 - int(remaining)
        self.mjlonirDownloadSignal.emit(step)


class MyWindow(QMainWindow):
    def __init__(self):
        super(MyWindow, self).__init__()
        uiPath = os.path.join(cwd+'\\UI', 'MJOLNIRUI.ui')
        uic.loadUi(uiPath, self)
        self.setWindowIcon(QIcon(os.path.join(cwd+'\\UI\\icons',
                                              'mjolnir.png')))
        self.setGeometry(890, 390, 1020, 640)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setFixedWidth(1020)
        self.setFixedHeight(640)
        self.temp = 0
        self.mjolnirThread = Mjolnir()
        self.mjolnirThread.mjlonirSignal.connect(self.finished)
        self.mjolnirThread.mjlonirException.connect(self.exceptionHandle)

        self.mjolnirDownloadThread = MjolnirDownload()
        (self.mjolnirDownloadThread.mjlonirDownloadSignal
                                   .connect(self.processDownload))
        (self.mjolnirDownloadThread.mjlonirDownloadException
                                   .connect(self.exceptionHandle))

        folderPath = os.path.join(cwd, 'MJOLNIR')
        self.savepath = os.path.expanduser(folderPath)
        self.label_5.setText(self.savepath)
        self.pushButton_2.setEnabled(False)
        self.show()

    @pyqtSlot()
    def on_pushButton_4_clicked(self):
        self.close()

    @pyqtSlot()
    def on_pushButton_clicked(self):
        self.temp = 0
        self.progressBar.setValue(0)
        self.mjolnirThread.youtubeURL = self.lineEdit.text()
        self.textBrowser.append("<span style='color:red'>Initializing links" +
                                "...</span>")
        iconPath = os.path.join(cwd+'\\UI\\lib', 'loading.gif')
        movie = QMovie(iconPath)
        self.label_2.setMovie(movie)
        movie.start()
        self.textBrowser.append("URL : " + str(self.mjolnirThread.youtubeURL))
        self.textBrowser.append("Waiting for response...")
        self.mjolnirThread.start()

    @pyqtSlot()
    def on_pushButton_3_clicked(self):
        self.savepath = str(QFileDialog.getExistingDirectory(self,
                                                             "Select Directory"
                                                             ))
        if self.savepath:
            self.label_5.setText(self.savepath)
        else:
            self.label_5.setText(cwd)

    @QtCore.pyqtSlot()
    def on_pushButton_2_clicked(self):
        self.textBrowser.append("Starting download...")
        self.textBrowser.append("<span style='color:orange'>Try <b>Best " +
                                "Available</b> in Quality, if unable to " +
                                "download within few seconds.</span>")
        self.mjolnirDownloadThread.youtubeURL = self.lineEdit.text()
        self.mjolnirDownloadThread.youtubeSavePath = self.savepath
        qchk = self.qualitycheck
        self.mjolnirDownloadThread.youtubeQuality = qchk.itemText(qchk
                                                                  .currentIndex
                                                                  ())
        self.mjolnirDownloadThread.start()

    def finished(self, yttitle, ytthumbnail):
        self.label_3.setText(yttitle)
        self.textBrowser.append("Response received!")
        image = QImage()
        image.loadFromData(ytthumbnail)
        rect = QRect(0, 12, 120, 66)
        image = image.copy(rect)
        self.label_2.setPixmap(QPixmap(image))
        self.pushButton_2.setEnabled(True)

    def processDownload(self, pushButton_2):
        self.progressBar.setValue(pushButton_2)
        if pushButton_2 >= 100 and self.temp == 0:
            self.temp = self.temp + 1
            self.downloadComplete()

    def speak(self, audio):
        engine = pyttsx3.init('sapi5')
        voices = engine.getProperty('voices')
        engine.setProperty('voice', voices[0].id)
        engine.say(audio)
        engine.runAndWait()

    def exceptionHandle(self, msg):
        if str(msg) == '<urlopen error [Errno 11001] getaddrinfo failed>':
            self.textBrowser.append("<span style='color:red'>Exception : " +
                                    "Unable to establish connection</span>")
        else:
            self.textBrowser.append("<span style='color:red'>Exception : " +
                                    msg + " </span>")
        failedIconPath = os.path.join(cwd+'\\UI\\lib', 'failed.jpg')
        self.label_2.setPixmap(QPixmap(failedIconPath))
        self.speak("Unable to download video")

    def downloadComplete(self):
        self.textBrowser.append("<span style='color:green'>Downloading " +
                                "Complete :)</span>")
        self.textBrowser_2.append("Downloaded : " + str(self.mjolnirThread
                                                            .youtubeTitle))
        self.pushButton_2.setEnabled(False)
        self.progressBar.setValue(0)
        self.speak("Video downloaded")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MyWindow()
    sys.exit(app.exec_())
