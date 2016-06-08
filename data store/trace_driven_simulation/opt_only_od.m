function [exist_cpu,exist_mem,cost] = opt_only_od(Ct, Mt)

global p_od_cpu;
global p_od_mem;

global window; %min
global t_start;
global t_end;

D = t_end; %duration in min


%------------------other variables---------------

exist_cpu = zeros(D, 1); %depending on hot/cold
exist_mem = zeros(D, 1); %depending on hot/cold

for t = t_start:t_end
    t
    if t>t_start
        exist_cpu(t) = exist_cpu(t-1);
        exist_mem(t) = exist_mem(t-1);
    end
        
    if (mod(t,window)==1) %the first minute of a control window
        k = (t-1)/window+1;% index of control window        
        exist_cpu(t) = Ct(k);
        exist_mem(t) = Mt(k);
    end
end
%-----------cost-------
s = 60;
r = t_start:t_end;
% cost = (p_od_cpu*exist_cpu(r) + p_od_mem*exist_mem(r))/s;
global cpu_spot;
global mem_spot;
global p_od;
od_vm = max(ceil(exist_cpu/cpu_spot),ceil(exist_mem/mem_spot));
cost = p_od*od_vm/s;


global H;
range = t_start:window:t_end;
file = fopen('./only_od/on_demand.txt','w');
% A = [exist_cpu(range) exist_mem(range) ones(length(range),1)*H ones(length(range),1)*(1-H)];
% for i = 1:length(range)
%     fprintf(file, '%d %f %f %f\n', A(i,:));
% end
A = [od_vm(range)*cpu_spot od_vm(range)*mem_spot ones(length(range),1)*H ones(length(range),1)*(1-H)];
for i = 1:length(range)
    fprintf(file, '%d %f %f %f\n', A(i,:));
end
fclose(file);

end
