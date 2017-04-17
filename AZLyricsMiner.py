import requests
import pickle
import re
import os
from time import time, sleep
import numpy as np

def GetWordsArtist(artist, single_songs = False):
	''' Creates .txt file with every word from all the lyrics
	of "artist" available on AZlyrics.com. For every artist
	a new directory is created.

	Parameters:
		
		artist : string of artist to search for. This string will be used
		in AZlyrics internal search engine, so it has to be as exact as
		that search engine needs

		single_songs : If True, every song that is found will get it's own
		.txt file with the lyrics, additionally to the .txt file mentioned above

	To avoid getting your IP banned from AZlyrics, every new song request
	is delayed by 15 + (15*np.random.rand()), so randomly between 15 and 30 seconds.
	This value was estimated empirically. This means the process can take some time,
	this is why this function will create two files "finished_links.txt" and 
	"unfinished_links.txt", so the process of mining the lyrics can be stopped and
	later started again without loss.
	'''

    assert isinstance(artist, str)
    headers = { 'User-Agent': 'Mozilla/5.0 (Windows NT 6.0; WOW64; rv:24.0) Gecko/20100101 Firefox/24.0' }

#   === Search for Artist and =================   
#   === Get Artist Page from Search Results ===

    search = re.sub(r" +", "+", artist)
    time1 = time()
    try:
        search_html = requests.get("http://search.azlyrics.com/search.php?q="+search, headers=headers).content
    except:
        raise Exception, "Could not connect to find artist"
    try:
        link, artist_name = ParseForArtistPage(search_html)
        artist_name = re.sub(r"^ +", "", artist_name)
        artist_name = re.sub(r" +$", "", artist_name)
    except:
        raise Exception, "Could not parse Search Page"
    print "Found Artist: %s" % artist_name
    
#   === Check/Make new Directory ===
    path = re.sub(r" ", "_", artist_name)
    if not os.path.exists(re.sub(r" ", "_", artist_name)):
        os.makedirs(path)
        print "Creating new Directory %s" %path
    else:
        print "Found Directory for %s" % artist_name
        
#   === Check wether link files exist, if not, make them ===
    try:
        unfinished_file = open("./"+path+"/"+"unfinished_links.txt", "rb")
        links = unfinished_file.readlines()
        unfinished_file.close()
        for i in range(len(links)):
            links[i] = links[i][:-2]
        unfinished_link_file_found = True
    except IOError as e:
        unfinished_link_file_found = False
    
    finished_links = []
    
    this_wait = np.random.rand()*15+15
    while time()-time1 < this_wait:
        print "\r" + "SLEEP ZzZ %2d" % (this_wait - (time() - time1)),
        sleep(0.1)
    time1 = time()
        
    if not unfinished_link_file_found:

#   === Get Songlist from Artist Page ===
        try:
            songlist_html = requests.get(link, headers=headers).content
        except:
            raise Exception, "Could not connect to get Songlist"
        try:
            songs, links_ordered = ParseSongs(songlist_html)
            order = np.random.permutation(range(len(links_ordered)))
            links = []
            for index in order:
                links.append(links_ordered[index])
        except:
            raise Exception, "Could not parse Artist Page for Songs"
        
    total = len(links)
    success = 0
    all_words = []
    
#   === Crawl all the songs ===
    current_song_no = 1
    while len(links) > 0:
        link = links.pop()
        this_wait = np.random.rand()*15+15
        while time()-time1 < this_wait:
            print "\r", "%3d / %3d" % (current_song_no, total), "   SLEEPING ZzZ", "  %2d" %  (this_wait-(time()-time1)),
            sleep(0.1)
        time1 = time()
        try:
            song_html = requests.get(link, headers=headers).content
        except Exception as e:
            print "\nCould not access %s" % link, e
            if "BadStatusLine" in str(e) and isinstance(e, requests.ConnectionError):
                print "No Internet Connection or IP Banned, stopping"
                links.append(link)
                break
            finished_links.append(link)
            continue
        try:
            title, text = ParseLyrics(song_html)
        except Exception as e:
            print "\nCould not parse %s" % link, e
            finished_links.append(link)
            continue
        if single_songs:
            titlepath = re.sub(r"^ +", "", title)
            titlepath = re.sub(r" +$", "", titlepath)
            titlepath = re.sub(r"\W", "", titlepath)
            titlepath = re.sub(r" +", "_", titlepath)
            f = open("./"+path+"/"+"%s.txt" % titlepath, "wb")
            f.write(title + "\r\n"*2)
            for line in text:
                f.write(line + "\r\n")
                for word in line.split():
                    all_words.append(word)
            f.close()
        else:
            for line in text:
                for word in line.split():
                    all_words.append(word)
        success += 1
        finished_links.append(link)
        current_song_no += 1
    finished_file = open("./"+path+"/"+"finished_links.txt", "ab")
    for link in finished_links:
        finished_file.write(link+"\r\n")
    finished_file.close()
    unfinished_file = open("./"+path+"/"+"unfinished_links.txt", "wb")
    for link in links:
        unfinished_file.write(link+"\r\n")
    unfinished_file.close()
    print "\nGot %d out of %d lyrics!" % (success, total)
    f = open("./"+path+"/"+"%s.txt" % re.sub(r" ", "_", artist_name+"_all"), "ab")
    for word in all_words:
        f.write(word+" ")
    f.close()
    return 0
    
def ParseForArtistPage(html):
	''' Parses a AZlyrics searchresult for the first found artist page

	Parameters:

		html : string of the html-file of searchresult

	Returns:

		link : string of link to artist page
		name : string of found artist name

	'''
    lines = lines = re.split(r"\r\n", html)
    for i, line in enumerate(lines):
        if "Sorry, your search returned <b>no results</b>" in line:
            raise Exception, "Sorry, your search returned no results!"
        if "<div class=\"panel-heading\"><b>Artist results:</b>" in line:
            break
    else:
        raise Exception, "No Parsing Results in Lines"
    while True:
        if "1. <a href=\"http://www.azlyrics.com/" in lines[i]:
            break
        i += 1
    link = re.findall(r"http\:.*\.html" ,lines[i])[0]
    name = re.findall(r"<b>.+</b>" ,lines[i])[0]
    name = name.split("<b>")[1].split("</b>")[0]
    return link, name
    
def ParseSongs(html):
	''' Parses a AZlyrics songlist (artist page) for links to lyrics

	Parameters:

		html : string of the html-file of songlist

	Returns:

		songs : list of song names as strings
		links : list of song links as string

	'''

    lines = re.split(r"\r\n", html)
    for i, line in enumerate(lines):
        if "var songlist" in line:
            break
    i += 1
    songslinks = lines[i].split("\n")
    songs = []
    links = []
    total, success = len(songslinks), len(songslinks)
    for song in songslinks:
        try:
            songs.append(re.findall(r"\{.+\}", song)[0].split("s:\"")[1].split("\"")[0])
            link = re.findall(r"\{.+\}", song)[0].split("h:\"")[1].split("\"")[0]
            links.append("http://www.azlyrics.com/lyrics/" + link.split("/lyrics/")[1])
        except IndexError:
            success -= 1
    print "Retrieved %d out of %d Links" % (success, total) 
    return songs, links
    
def ParseLyrics(html):
	''' Parses a AZlyrics song page for lyrics

	Parameters:

		html : string of the html-file of song page

	Returns:

		title : title of song as string
		test : song text as string

	'''
    lines = re.split(r"\r\n", html)
    for i, line in enumerate(lines):
        if "<!-- Usage of azlyrics.com content by any third-party lyrics provider is prohibited by our licensing agreement. Sorry about that. -->" in line:
            break
    title = lines[i-4].split("\"")[1]
    i += 1
    text = re.split(r"<br>\n", lines[i])
    for i in range(len(text)):
        text[i] = re.sub(r"<.+?>", "", text[i])
        text[i] = re.sub(r"\[.+?\]", "", text[i])
        text[i] = re.sub(r"\n", "", text[i])
        text[i] = re.sub(r"^ +", "", text[i])
    return title, text
#
#
#
#
#
#
#
#