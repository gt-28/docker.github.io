import urllib2
from bs4 import BeautifulSoup
from subprocess import call
import imghdr
import shutil
import base64

call(["rm", "-rf", "kb"])
call(["mkdir", "kb"])
call(["mkdir", "kb/images"])
requrl = "https://success.docker.com/@api/deki/pages/"
response = urllib2.urlopen(requrl)
soup = BeautifulSoup(response, 'lxml')
for page in soup.find_all('page'):
    fileout = '';
    skipme = False
    if str(type(page.path.string)) == "<class 'bs4.element.NavigableString'>":
        if page.path.string.find("Internal") > -1:
            skipme = True
            print 'Skipping ' + page['id'] + ' because path=' + page.path.string
    if skipme == False:
        requrl = 'https://success.docker.com/@api/deki/pages/' + page['id']
        pagemetadata = urllib2.urlopen(requrl)
        metadatasoup = BeautifulSoup(pagemetadata, 'lxml')
        fileout += '---\n'
        fileout += 'title: \"' + page.title.string.replace('"','') + '\"\n'
        fileout += 'id: ' + page['id'] + '\n'
        fileout += 'draftstate: ' + page['draft.state'] + '\n'
        fileout += 'deleted: '  + page['deleted'] + '\n'
        fileout += 'source: https://success.docker.com/@api/deki/pages/' + page['id'] + '/contents' + '\n'
        fileout += 'tags:' + '\n'
        for thistag in metadatasoup.find_all('tag'):
            fileout += '- tag: \"' + thistag['value'] + '\"' + '\n'
        fileout += '---' + '\n'
        fileout += '{% raw %}\n'

        requrl = 'https://success.docker.com/@api/deki/pages/' + page['id'] + '/contents'
        pagecontents = urllib2.urlopen(requrl)
        contentsoup = BeautifulSoup(pagecontents, 'html.parser')
        rawhtml = BeautifulSoup(contentsoup.get_text(), 'html.parser')
        # kill "No headers" <em> instances
        ems = rawhtml.find_all('em')
        for em in ems:
            if em.text.strip() == 'No headers':
                em.extract()
        # kill ending nav OL lists
        internals = rawhtml.find_all(attrs={"rel":"internal"})
        for thisin in internals:
            if thisin.name=='a':
                if thisin['href'][0]=="#":
                    if thisin.parent.parent.name=="ol":
                        thisin.parent.parent.extract()
        # save all images
        user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
        headers = { 'User-Agent' : user_agent }
        images = rawhtml.find_all('img')
        imageIndex = 0
        for img in images:
            imgRequest = urllib2.Request(img['src'], headers=headers)
            try:
                imgData = urllib2.urlopen(imgRequest).read()
            except urllib2.URLError, e:
                if e.args[0]=='unknown url type: data':
                    rawimgdata = img['src']
                    head, data = rawimgdata.split(',', 1)
                    file_ext = head.split(';')[0].split('/')[1]
                    imgData = base64.b64decode(data)
            newFileName = 'kb/images/' + page['id'] + '-' + str(imageIndex)
            output = open(newFileName,'wb')
            output.write(imgData)
            output.close()
            newImageFileExt = imghdr.what(newFileName)
            shutil.move(newFileName, newFileName + '.' + newImageFileExt)
            img['src'] = '/' + newFileName + '.' + newImageFileExt
            print 'Saved: ' + newFileName + '.' + newImageFileExt
            imageIndex = imageIndex + 1
        fileout += rawhtml.prettify() + '\n'
        fileout += '{% endraw %}\n'
        f = open('kb/' + page['id'] + '.html', 'w+')
        f.write(fileout.encode('utf8'))
        f.close
        print 'Success writing kb/' + page['id'] + '.html'
