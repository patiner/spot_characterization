close all;
clear all;

%  determine the workload partition: hot v.s. cold at each market
%  (including on-demand)

partition_prop = 1;
only_od = 0;

% load Lb.mat; %(T,B)  B = s1b1,s1b2,s2b1,s2b2,od
% load ES.mat;

global cpu_spot;
cpu_spot = 4;
global mem_spot;
mem_spot = 15;
global p_od;
p_od = 0.266; 
%m3.large=0.133    2   7.5
% m3xl=0.266      4   15
% c3l=0.105     2    3.75
% c32xl=0.42    8    15

% type = 'm3.large';
% region = 'us-west';
% fname = ['./trace/' type '/' region '/Lb_CDF.mat'];
% load(fname);
% fname = ['./trace/' type '/' region '/ES_CDF.mat'];
% load(fname);
% Lb = Lb_CDF;
% ES = ES_CDF;

type = 'm3.xlarge';
region = 'us-west'; 

fname = ['./trace/' type '/' region '/Lb_max.mat'];
load(fname);
fname = ['./trace/' type '/' region '/ES_max.mat'];
load(fname);
Lb = Lb_max;
ES = ES_max;

fname = ['./trace/' type '/' region '/price.mat'];
load(fname); % (2,T)



load Ct.mat; %num of cores
load Mt.mat; %ram in GB

% Ct = ones(length(Ct),1)*ceil(mean(Ct));
% Ct = ceil(rand(length(Ct),1)*1.2.*Ct);
% Mt = ceil(rand(length(Mt),1)*1.2.*Mt);

global p_od_cpu;
p_od_cpu = 0.0246;
global p_od_mem;
p_od_mem = 0.0036;

global H;
H = 1;

global bid;
bid = [p_od 5*p_od p_od 5*p_od p_od];

global window;
window = 60; %min
global t_start;
global t_end;
% t_start = 24*60*27+1;
% t_end = 24*60*50;
t_start = 24*60*7+1; %the first 7 days as initial training data
t_end = 24*60*90;
% t_end = 129581; % only for c3.large





%------------------other variables---------------
global temp_cpu;
global temp_mem;
temp_cpu = zeros(5,1);
temp_mem = zeros(5,1);
global lbound;
global ubound;
lbound = zeros(20,1);
ubound = ones(20,1);
%-------------- proposed---------
if partition_prop == 1
    
    [exist_cpu_prop,exist_mem_prop,spot_vm_prop,x_prop,y_prop,hot_fail_prop,cold_fail_prop,cost_prop] = opt_partition_prop(Lb, ES, price, Ct, Mt);
        
    total_cost_prop = sum(cost_prop,2); %time-series
    total_cost_split_prop = sum(cost_prop,1);
    total_cost_value_prop = sum(total_cost_split_prop);
    
    hot_fail_total_prop = sum(hot_fail_prop,2);   %perf. degradation is proportional to failure data; do not consider mis-prediction
    cold_fail_total_prop = sum(cold_fail_prop,2);
    
    fname = ['./trace/' type '/' region '/opt_max.mat'];
%     fname = ['./trace/' type '/' region '/opt_CDF.mat'];
% fname = ['./trace/' type '/' region '/opt_prop_new.mat'];
    save(fname);
end
%--------------onlyOD--------------------------------
if only_od == 1    
    [exist_cpu_only_od,exist_mem_only_od,cost_only_od] = opt_only_od(Ct, Mt);
    
    total_cost_value_only_od = sum(cost_only_od); 
    fname = ['./trace/' type '/' region '/opt_od.mat'];
    save(fname);
end
