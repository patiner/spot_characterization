close all;
clear all;

type = 'm3.xlarge';
region = 'us-east';
fname = ['./' type '/' region '-1c/' type '.txt'];
load(fname);
pc = m3_xlarge(:,1);
fname = ['./' type '/' region '-1d/' type '.txt'];
load(fname);
pd = m3_xlarge(:,1);
% load './m3.xlarge/us-east-1c/m3.xlarge.txt';
% load './m3.xlarge/us-east-1d/m3.xlarge.txt';


%us-east   m3l=0.133,   m3xl=0.266, c3l=0.105,  c32xl=0.42
%us-west oregon   m3l=0.133,   m3xl=0.266, c3l=0.105,  c32xl=0.42
p_od = 0.266;

T = 90*24; %hours
H = 24*60; %history window


LB_OD_CDF_c = zeros(T,1);
LB_5OD_CDF_c = zeros(T,1);
ES_OD_CDF_c = zeros(T,1);
ES_5OD_CDF_c = zeros(T,1);

LB_OD_CDF_d = zeros(T,1);
LB_5OD_CDF_d = zeros(T,1);
ES_OD_CDF_d = zeros(T,1);
ES_5OD_CDF_d = zeros(T,1);

for t = 24*7+1:T
    history_c = pc((t-1)*60-H+1:(t-1)*60);
    [LB_OD_CDF_c(t), ES_OD_CDF_c(t)] = get_LB_ES_CDF(history_c,p_od,1440);
    [LB_5OD_CDF_c(t), ES_5OD_CDF_c(t)] = get_LB_ES_CDF(history_c,5*p_od,1440);
    
    history_d = pd((t-1)*60-H+1:(t-1)*60);
    [LB_OD_CDF_d(t), ES_OD_CDF_d(t)] = get_LB_ES_CDF(history_d,p_od,1440);
    [LB_5OD_CDF_d(t), ES_5OD_CDF_d(t)] = get_LB_ES_CDF(history_d,5*p_od,1440); 
end

Lb_CDF = [LB_OD_CDF_c LB_5OD_CDF_c LB_OD_CDF_d LB_5OD_CDF_d ones(T,1)*14400000];
ES_CDF = [ES_OD_CDF_c ES_5OD_CDF_c ES_OD_CDF_d ES_5OD_CDF_d ones(T,1)*p_od];
% save('Lb_CDF.mat','Lb_CDF');
% save('ES_CDF.mat','ES_CDF');
fdir = ['./' type '/' region '/'];
save([fdir 'Lb_CDF.mat'],'Lb_CDF');
save([fdir 'ES_CDF.mat'],'ES_CDF');


% figure;
% plot(LB_OD_CDF_d)
% hold on;
% plot(LB_5OD_CDF_d,'r');
% hold off;
% 
% figure;
% plot(ES_OD_CDF_d)
% hold on;
% plot(ES_5OD_CDF_d,'r');
% hold off;


