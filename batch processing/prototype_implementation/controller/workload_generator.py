from random import randint

lambda_min = 8
lambda_max = 10
length_min = 30
length_max = 800

hours = 24*80

with open('workload.txt', 'w') as f:
    for i in range(hours):
        arr_rate = randint(lambda_min, lambda_max)
        job_list = []
        for j in range(arr_rate):
            job_list.append(randint(length_min, length_max))

        f.write(','.join(str(j) for j in job_list) + '\n')

