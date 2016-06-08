function [ ES ] = find_ES( data, b )
%UNTITLED4 Summary of this function goes here
%   b is bid price
% return the length of occurences of L(b)

n = length(data);
ES = [];

is_lower = false;

l = [];


for i = 1:n
    
    if data(i)<=b
        if i < n
            if is_lower == false
                l = [data(i)];
                is_lower = true;
            else
                l = [l data(i)];
            end
        else %the last day
            if is_lower == false
                l = [l data(i)];
            else
                l = [l data(i)];
            end
            ES = [ES mean(l)];
        end
    else % higher than bid
        if is_lower == true
            ES = [ES mean(l)];
            l = [];
            is_lower = false;
        end
    end
    
end

if length(ES)==0
    ES = 0;
end


end

