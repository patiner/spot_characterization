__author__ = 'cheng'
from datetime import datetime
import time

def convert_time(dir, type):

    #ff = 'us-west-1a/c3.2xlarge.txt'

    f_in = './%s/%s.txt'%(dir,type)
    print f_in
    f_out = './%s/extracted_%s.txt'%(dir,type)
    print f_out
    f_write = open(f_out,'w+')
    f_read = open(f_in)

    start = True

    for line in reversed(f_read.readlines()):
        #print line
        temp = line.rstrip()
        t_price = temp.split('\t')[1]
        x = temp.split('\t')[2]
        t_date = '%s %s'%(x[:10],x[11:19])
        x_date = datetime.strptime(t_date, "%Y-%m-%d %H:%M:%S")
        t_seconds = time.mktime(x_date.timetuple())

        if start==True:
            t_minute = 1
            t_start_second = t_seconds
            start = False
        else:
            delta_minute = int(round(float(t_seconds-t_start_second)/60.0))
            t_minute = delta_minute+1

        str = '%s\t%s\t%d\t%d\n'%(t_price,t_date,t_seconds,t_minute)
        #print str
        f_write.write(str)


    f_write.close()

def main():
    dir = ['us-east-1b', 'us-east-1c', 'us-east-1d', 'us-east-1e', 'us-west-1a', 'us-west-1c']
    type = ['c3.2xlarge', 'c3.4xlarge', 'c3.8xlarge', 'c3.large', 'm3.2xlarge', 'm3.large', 'm3.medium', 'm3.xlarge', 'r3.2xlarge', 'r3.4xlarge', 'r3.8xlarge', 'r3.large', 'r3.xlarge']
    for i in dir:
        for j in type:
            convert_time(i, j)

if __name__ == "__main__":
    main()

