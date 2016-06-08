% od_cpu = zeros(25,1);
% od_mem = zeros(25,1);
% od_hot = zeros(25,1);
% od_cold = zeros(25,1);
% % ss = 24*60*67+1;
% ss = 24*60*67+1-60;
% 
% for i = 1:25
%     od_cpu(i) = exist_cpu_prop(ss+(i-1)*60,5);
%     od_mem(i) = exist_mem_prop(ss+(i-1)*60,5);
%     od_hot(i) = x_prop(ss+(i-1)*60,5)*0.6;
%     od_cold(i) = x_prop(ss+(i-1)*60,5)*0.4;
% end
% 
% od_input = [od_cpu od_mem od_hot od_cold];

% index = 4; %1: us-east-1c-od   2: us-east-1c-5od  3: us-east-1d-od  4: us-east-1d-5od   
% spot_num = zeros(25,1);
% spot_hot = zeros(25,1);
% spot_cold = zeros(25,1);
% % ss = 24*60*67+1;
% ss = 24*60*67+1-60;
% 
% for i = 1:25
%     spot_num(i) = spot_vm_prop(ss+(i-1)*60,index);
%     
%     spot_hot(i) = x_prop(ss+(i-1)*60,index)*0.6;
%     spot_cold(i) = x_prop(ss+(i-1)*60,index)*0.4;
% end

% spot_input = [spot_num spot_hot spot_cold];

od_cpu = zeros(25,1);
od_mem = zeros(25,1);
od_hot = zeros(25,1);
od_cold = zeros(25,1);
% ss = 24*60*67+1;
ss = 24*60*67+1-60;

for i = 1:25
    od_cpu(i) = exist_cpu_only_od(ss+(i-1)*60,1);
    od_mem(i) = exist_mem_only_od(ss+(i-1)*60,1);
    od_hot(i) = x_prop(ss+(i-1)*60,1)*0.6;
    od_cold(i) = x_prop(ss+(i-1)*60,1)*0.4;
end

od_input = [od_cpu od_mem od_hot od_cold];

od_num = max(ceil(od_cpu/2),ceil(od_mem/7.5));

