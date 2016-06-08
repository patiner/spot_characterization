function [x,y,delta_cpu,delta_mem,new_cpu,new_mem] = find_opt(Ct, Mt,Lb, ES_cpu, ES_mem)
%total_cpu and total_mem are the states: num of existing cpus and mem
%Ct and Mt are pred. res. demand
% sol = hot;cold;delta_cpu; z where z = max{0,-R_msb}. 5 markets (2Az*2bid+od),
% so 20 variables in total. s1b1,s1b2,s2b1,s2b2,od

%-----parameters
global temp_cpu;
global temp_mem;
global lbound;
global ubound;
global H;
% H = 1;
alpha = 0.2;
beta = 0.1;
eta = 0.01;
% eta = 100;
T = 1;

%------------------
f = ones(1,20);  %coefficient vector
f(1:10) = Mt*T*[ES_mem ES_mem]+[alpha*ones(1,5) beta*ones(1,5)]*Mt./[Lb Lb];
f(11:15) = T*ES_cpu;
f(16:20) = eta*ones(5,1);
%----
A1 = [diag(ones(1,5)*Ct) diag(ones(1,5)*Ct) diag(-ones(1,5)) diag(zeros(1,5))];
A2 = [diag(-Mt*ones(1,5)) diag(-Mt*ones(1,5)) diag(zeros(1,5)) diag(-ones(1,5))];
A = [A1; A2];
b = [temp_cpu;-temp_mem];
%----------------x5+y5>=0.05;  lower bound on od
A_temp = zeros(1,20);
A_temp(5) = -1;
A_temp(10) = -1;
A = [A;A_temp];
b_temp = -0.1;
b = [b;b_temp];
%----------------
Aeq = zeros(2,20);
Aeq(1,1:5) = ones(1,5);
Aeq(2,6:10) = ones(1,5);
beq = [H; 1-H];
%----
for i = 1:4
    if Lb(i)<60
        ubound(i) = 0;
        ubound(i+5) = 0;
    end
end
if Lb(1)<60 && Lb(2)<60 && Lb(3)<60 && Lb(4)<60
    ubound(5) = H;
    ubound(10) = 1-H;
    lbound(5) = H;
    lbound(10) = 1-H;
end

ubound(11:15) = max(ones(5,1)*Ct,temp_cpu);  %upper bound of extra cpu resource
ubound(16:20) = max(ones(5,1)*Mt,temp_mem);  %uppper bound of extra mem
lbound(11:15) = -temp_cpu;
%----
intcon = [11 12 13 14 15];
%----
sol = intlinprog(f, intcon, A, b, Aeq, beq, lbound, ubound);
%------
x = sol(1:5)';
y = sol(6:10)';
delta_cpu = sol(11:15)';
z = sol(16:20);
%----
delta_mem = Mt*(x+y)-temp_mem';
new_cpu = temp_cpu'+delta_cpu; %may need to round up; column vector
new_cpu(5) = round(new_cpu(5));
new_mem = temp_mem' + delta_mem;

end