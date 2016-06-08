function [ Lb, start_pts ] = find_Lb( data, b )
%UNTITLED4 Summary of this function goes here
%   b is bid price
% return the length of occurences of L(b)


n = length(data);
Lb = [];
start_pts = [];

is_lower = false;

l = 0;

for i = 1:n
    
    if data(i)<=b
        if i < n
            if is_lower == false
                l = 1;
                is_lower = true;
                start_pts = [start_pts i];
            else
                l = l + 1;
            end
        else
            if is_lower == false
                l = 1;  
                start_pts = [start_pts i];
            else
                l = l + 1;
            end
            Lb = [Lb l];
        end
    else
        if is_lower == true
            Lb = [Lb l];
            is_lower = false;
        end
    end
    
end

if length(Lb)==0
    Lb = 0;
end


end

