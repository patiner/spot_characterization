__author__ = 'cheng'

import math

def convert_time(dir, type):

    #ff = 'us-west-1a/c3.2xlarge.txt'

    f_in = './%s/extracted_%s.txt'%(dir, type)
    f_out = './%s/price_time_%s.txt'%(dir, type)
    f_write = open(f_out,'w+')
    f_read = open(f_in)

    start = True

    line = f_read.readline()
    while line:
        t_price = line.split('\t')[0]
        print(line)
        t_minute = int(line.split('\t')[3])

        if start==True:
            start = False
        else:
            for i in range(t_minute_pre,t_minute):
                str = '%s\t%d\n'%(t_price_pre,i)
                #print str
                f_write.write(str)

        t_minute_pre = t_minute
        t_price_pre = t_price
        line = f_read.readline()

    f_write.close()

def main():
    dir = ['us-east-1b', 'us-east-1c', 'us-east-1d', 'us-east-1e', 'us-west-1a', 'us-west-1c']
    type = ['c3.2xlarge', 'c3.4xlarge', 'c3.8xlarge', 'c3.large', 'm3.2xlarge', 'm3.large', 'm3.medium', 'm3.xlarge', 'r3.2xlarge', 'r3.4xlarge', 'r3.8xlarge', 'r3.large', 'r3.xlarge']
    for i in dir:
        for j in type:
            convert_time(i, j)

if __name__ == "__main__":
    main()
