import traceback
import praw
import time
import datetime
import sqlite3

print('Connecting to reddit')
r = praw.Reddit('/u/GoldenSights automatic timestamp search program')

def get_all_posts(subreddit, lower=None, maxupper=None, interval=86400):
    databasename = subreddit + '.db'
    sql = sqlite3.connect(databasename)
    cur = sql.cursor()
    cur.execute(('CREATE TABLE IF NOT EXISTS posts(idint INT, idstr TEXT, '
    'created INT, self INT, nsfw INT, author TEXT, title TEXT, '
    'url TEXT, selftext TEXT, score INT, subreddit TEXT, distinguish INT, '
    'textlen INT, num_comments INT, flair_text TEXT, flair_css_class TEXT)'))
    #  0 - idint
    #  1 - idstr
    #  2 - created
    #  3 - self
    #  4 - nsfw
    #  5 - author
    #  6 - title
    #  7 - url
    #  8 - selftext
    #  9 - score
    # 10 - subreddit
    # 11 - distinguished
    # 12 - textlen
    # 13 - num_comments
    # 14 - flair_text
    # 15 - flair_css_class

    offset = -time.timezone
    subname = subreddit if type(subreddit)==str else subreddit.display_name
    if lower==None or maxupper==None:
        if isinstance(subreddit, praw.objects.Subreddit):
            creation = subreddit.created_utc
        else:
            subreddit = r.get_subreddit(subreddit)
            creation = subreddit.created_utc
    
        nowstamp = datetime.datetime.now(datetime.timezone.utc).timestamp()
        lower = creation
        maxupper = nowstamp
        
    #outfile = open('%s-%d-%d.txt'%(subname, lower, maxupper), 'w', encoding='utf-8')
    #lower -= offset
    maxupper -= offset
    cutlower = lower
    cutupper = maxupper
    upper = lower + interval
    itemcount = 0

    while lower < maxupper:
        print('\nCurrent interval:', interval, 'seconds')
        print('Lower', datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(lower), "%b %d %Y %H:%M:%S"), lower)
        print('Upper', datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(upper), "%b %d %Y %H:%M:%S"), upper)
        timestamps = [lower, upper]
        while True:
            try:
                searchresults = list(r.search('', subreddit=subreddit, sort='new', timestamps=timestamps, limit=100))
                break
            except:
                traceback.print_exc()
                print('resuming in 5...')
                time.sleep(5)
        print([i.id for i in searchresults])
        smartinsert(sql, cur, searchresults)
        itemcount += len(searchresults)
        print('Found', len(searchresults), ' items')
        if len(searchresults) < 5:
            print('Too few results, doubling interval', end='')
            interval *= 2
        if len(searchresults) > 95:
            print('Too many results, halving interval', end='')
            interval /= 2
            upper = lower + interval
        else:
            lower = upper
            upper = lower + interval
        print()

    print('Ended with %d items in %s' % (itemcount, databasename))


def smartinsert(sql, cur, results):
    for o in results:
        cur.execute('SELECT * FROM posts WHERE idint=?', [b36(o.id)])
        if not cur.fetchone():
            try:
                o.authorx = o.author.name
            except AttributeError:
                o.authorx = '[DELETED]'

            postdata = [b36(o.id), o.id, o.created_utc, o.is_self, o.over_18,
            o.authorx, o.title, o.url, o.selftext, o.score,
            o.subreddit.display_name, o.distinguished, len(o.selftext),
            o.num_comments, o.link_flair_text, o.link_flair_css_class]
            cur.execute('INSERT INTO posts VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', postdata)
            sql.commit()


def base36encode(number, alphabet='0123456789abcdefghijklmnopqrstuvwxyz'):
    """Converts an integer to a base36 string."""
    if not isinstance(number, (int)):
        raise TypeError('number must be an integer')
    base36 = ''
    sign = ''
    if number < 0:
        sign = '-'
        number = -number
    if 0 <= number < len(alphabet):
        return sign + alphabet[number]
    while number != 0:
        number, i = divmod(number, len(alphabet))
        base36 = alphabet[i] + base36
    return sign + base36

def base36decode(number):
    return int(number, 36)

def b36(i):
    if type(i) == int:
        return base36encode(i)
    if type(i) == str:
        return base36decode(i)

print("Get posts from subreddit: /r/", end='')
sub = input()
print('Lower bound (Leave blank to get ALL POSTS)\n]: ', end='')
lower  = input()
if lower == '':
    x = get_all_posts(sub)
else:
    print('Maximum upper bound\n]: ', end='')
    maxupper = input()
    print('Starting interval (Leave blank for standard)\n]: ', end='')
    interval = input()
    if interval == '':
        interval = 84600
    try:
        maxupper = int(maxupper)
        lower = int(lower)
        interval = int(interval)
        x = get_all_posts(sub, lower, maxupper, interval)
    except ValueError:
        print("lower and upper bounds must be unix timestamps")
        input()
print("Done. Press Enter to close window")
input()
quit()