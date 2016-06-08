function [exist_cpu,exist_mem,spot_vm,x,y,hot_fail,cold_fail,cost] = opt_partition_prop(Lb, ES, price, Ct, Mt)



global p_od_cpu;
global p_od_mem;

global p_od; %m3.large

global bid;

global window; %min
global t_start;
global t_end;

B = length(bid); %number of bids
D = t_end; %duration in min

global cpu_spot;
global mem_spot;

%------------------other variables---------------
global temp_cpu;
global temp_mem;
temp_cpu = zeros(5,1);
temp_mem = zeros(5,1);
global lbound;
global ubound;
lbound = zeros(20,1);
ubound = ones(20,1);

%--------------control variables--------------
x = zeros(D, B); %the last row is for on-demand
y = zeros(D, B);
exist_cpu = zeros(D, B); %depending on hot/cold
exist_mem = zeros(D, B); %depending on hot/cold
%     delta_cpu = zeros(D, B); %depending on hot/cold
%     delta_mem = zeros(D, B); %depending on hot/cold
spot_vm = zeros(D,B-1);

%---------------------
hot_fail = zeros(D,B-1);
cold_fail = zeros(D,B-1);
%----------------------------------------------
for t = t_start:t_end
    t
    
    if t==39850
        aa = 3;
    end
    
    lbound = zeros(20,1);
    ubound = ones(20,1);
    if t==t_start
        ubound(1:4) = [0; 0; 0; 0]; %only use od at the beginning
        ubound(6:9) = [0; 0; 0; 0];
    else
        exist_cpu(t,:) = exist_cpu(t-1,:);
        exist_mem(t,:) = exist_mem(t-1,:);
        x(t,:) = x(t-1,:);
        y(t,:) = y(t-1,:);
        %update total_cpu and total_mem
        if price(t,1)>bid(1) && price(t-1,1)<=bid(1) %bid fails
            exist_cpu(t,5) = exist_cpu(t,5) + exist_cpu(t,1);
            exist_mem(t,5) = exist_mem(t,5) + exist_mem(t,1);
            exist_cpu(t,1) = 0;
            exist_mem(t,1) = 0;
            ubound([1 6]) = [0;0];
            x(t,5) = x(t,5) + x(t,1);
            y(t,5) = y(t,5) + y(t,1);
            x(t,1) = 0;
            y(t,1) = 0;
        else
            exist_mem(t,1) = exist_mem(t-1,1);
            exist_cpu(t,1) = exist_cpu(t-1,1);
            x(t,1) = x(t-1,1);
            y(t,1) = y(t-1,1);
        end
        if price(t,1)>bid(2) && price(t-1,1)<=bid(2) %bid fails
            exist_cpu(t,5) = exist_cpu(t,5) + exist_cpu(t,2);
            exist_mem(t,5) = exist_mem(t,5) + exist_mem(t,2);
            exist_cpu(t,2) = 0;
            exist_mem(t,2) = 0;
            ubound([2 7]) = [0;0];
            x(t,5) = x(t,5) + x(t,2);
            y(t,5) = y(t,5) + y(t,2);
            x(t,2) = 0;
            y(t,2) = 0;
        else
            exist_cpu(t,2) = exist_cpu(t-1,2);
            exist_mem(t,2) = exist_mem(t-1,2);
            x(t,2) = x(t-1,2);
            y(t,2) = y(t-1,2);
        end
        if price(t,2)>bid(3) && price(t-1,2)<=bid(3)%bid fails
            exist_cpu(t,5) = exist_cpu(t,5) + exist_cpu(t,3);
            exist_mem(t,5) = exist_mem(t,5) + exist_mem(t,3);
            exist_cpu(t,3) = 0;
            exist_mem(t,3) = 0;
            ubound([3 8]) = [0;0];
            x(t,5) = x(t,5) + x(t,3);
            y(t,5) = y(t,5) + y(t,3);
            x(t,3) = 0;
            y(t,3) = 0;
        else
            exist_cpu(t,3) = exist_cpu(t-1,3);
            exist_mem(t,3) = exist_mem(t-1,3);
            x(t,3) = x(t-1,3);
            y(t,3) = y(t-1,3);
        end
        if price(t,2)>bid(4) && price(t-1,2)<=bid(4)%bid fails
            exist_cpu(t,5) = exist_cpu(t,5) + exist_cpu(t,4);
            exist_mem(t,5) = exist_mem(t,5) + exist_mem(t,4);
            exist_cpu(t,4) = 0;
            exist_mem(t,4) = 0;
            ubound([4 9]) = [0;0];
            x(t,5) = x(t,5) + x(t,4);
            y(t,5) = y(t,5) + y(t,4);
            x(t,4) = 0;
            y(t,4) = 0;
        else
            exist_cpu(t,4) = exist_cpu(t-1,4);
            exist_mem(t,4) = exist_mem(t-1,4);
            x(t,3) = x(t-1,3);
            y(t,3) = y(t-1,3);
        end
    end
    temp_cpu = exist_cpu(t,:)';
    temp_mem = exist_mem(t,:)';
    
    if (mod(t,window)==1) %the first minute of a control window
        k = (t-1)/window+1;% index of control window
        %             [x(t,:),y(t,:),delta_cpu(t,:),delta_mem(t,:),exist_cpu(t,:),exist_mem(t,:)] = find_opt(Ct(k),Mt(k),Lb(k,:),ES(k,:)/p_od*p_od_cpu,ES(k,:)/p_od*p_od_mem);
        [x(t,:),y(t,:),~,~,exist_cpu(t,:),exist_mem(t,:)] = find_opt(Ct(k),Mt(k),Lb(k,:),ES(k,:)/p_od*p_od_cpu,ES(k,:)/p_od*p_od_mem);
        ubound = ones(20,1);
    end
    %translate into VMs for spot instance
    for i = 1:4
        spot_vm(t,i) = max(ceil(exist_cpu(t,i)/cpu_spot),ceil(exist_mem(t,i)/mem_spot));
        exist_cpu(t,i) = spot_vm(t,i)*cpu_spot;
        exist_mem(t,i) = spot_vm(t,i)*mem_spot;
    end
    
    if t>t_start
        k = floor((t-1)/window)+1;% index of control window
        if price(t,1)>bid(1) && price(t-1,1)<=bid(1) %bid fails
            hot_fail(t,1) = x(t-1,1)*Mt(k);
            cold_fail(t,1) = y(t-1,1)*Mt(k);
        end
        if price(t,1)>bid(2) && price(t-1,1)<=bid(2) %bid fails
            hot_fail(t,2) = x(t-1,2)*Mt(k);
            cold_fail(t,2) = y(t-1,2)*Mt(k);
        end
        if price(t,2)>bid(3) && price(t-1,2)<=bid(3) %bid fails
            hot_fail(t,3) = x(t-1,3)*Mt(k);
            cold_fail(t,3) = y(t-1,3)*Mt(k);
        end
        if price(t,2)>bid(4) && price(t-1,2)<=bid(4) %bid fails
            hot_fail(t,4) = x(t-1,4)*Mt(k);
            cold_fail(t,4) = y(t-1,4)*Mt(k);
        end
    end
end

%-----------cost-------

s = 60;
r = t_start:t_end;
cost = zeros(length(r),B);
cost(:,1) = price(r,1).*spot_vm(r,1)/s;
cost(:,2) = price(r,1).*spot_vm(r,2)/s;
cost(:,3) = price(r,2).*spot_vm(r,3)/s;
cost(:,4) = price(r,2).*spot_vm(r,4)/s;
% cost(:,5) = (p_od_cpu*exist_cpu(r,5) + p_od_mem*exist_mem(r,5))/s;
cost(:,5) = p_od*max(ceil(exist_cpu(r,5)/cpu_spot),ceil(exist_mem(r,5)/mem_spot))/s;

% total_cost = sum(cost,2); %time-series
% total_cost_split = sum(cost,1);
% total_cost_value = sum(total_cost_split);
% 
% hot_fail_total = sum(hot_fail,2);   %perf. degradation is proportional to failure data; do not consider mis-prediction
% cold_fail_total = sum(cold_fail,2);

%---------------plot-----------
% figure;
% plot(spot_vm(t_start:t_end,:));
% hold on;
% plot(exist_cpu(t_start:t_end,5),'k');
% hold off;
% figure;
% plot(exist_mem(t_start:t_end,5),'k');

%---------write to file-------
range = t_start:window:t_end;
file = fopen('./prop/us_east_1c_1OD.txt','w');
A = [spot_vm(range,1) x(range,1) y(range,1)];
for i = 1:length(range)
    fprintf(file, '%d %f %f\n', A(i,:));
end
fclose(file);

file = fopen('./prop/us_east_1c_5OD.txt','w');
A = [spot_vm(range,2) x(range,2) y(range,2)];
for i = 1:length(range)
    fprintf(file, '%d %f %f\n', A(i,:));
end
fclose(file);

file = fopen('./prop/us_east_1d_1OD.txt','w');
A = [spot_vm(range,3) x(range,3) y(range,3)];
for i = 1:length(range)
    fprintf(file, '%d %f %f\n', A(i,:));
end
fclose(file);

file = fopen('./prop/us_east_1d_5OD.txt','w');
A = [spot_vm(range,4) x(range,4) y(range,4)];
for i = 1:length(range)
    fprintf(file, '%d %f %f\n', A(i,:));
end
fclose(file);

file = fopen('./prop/on_demand.txt','w');
A = [exist_cpu(range,5) exist_mem(range,5) x(range,5) y(range,5)];
for i = 1:length(range)
    fprintf(file, '%d %f %f %f\n', A(i,:));
end
fclose(file);


end