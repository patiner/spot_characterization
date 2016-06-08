function [ LB_overestimate, ES_diff ] = get_LB_overestimate_f( price, bid, window_length )
    % with moving window

    
    %mkdir(dst_path);
%     price = load([path filename]);
%     price = price(:,1);
    %price = price_time_c3_large(:,1);

    D = 90;
    scalar = [0.1 0.5 1 2 5 10];
    B = scalar*bid; %6 bids
    duration_dist = cell(length(B),D);
    price_dist = cell(length(B), D);
    %daily

    % for each bid
    for j = 1:length(B)
        % start condition: start from the 7th day and compute L(b) in the
        % first 7 days
        for i = window_length:D
            duration = [];
            ES = [];
            % for each day in the window
            for k = 1:window_length
                % start condition: start from the i - window_length day
                % to i - windows_length + 1 day
                data = price((i-window_length+k-1)*1440+1:(i-window_length+k)*1440);

                duration = [duration find_Lb(data,B(j))];
                ES = [ES find_ES_new(data,B(j))];
            end
            duration_dist{j,i} = duration;
            price_dist{j,i} = ES;

        end

    end

    %------------------- output hoursly record
    % p_LB_list = zeros(6,90);
    % p_ES_list = zeros(6,90);
    % 
    % for k = 1:6
    %     for i = 7:90
    %         p_LB_list(k,i) = predict_LB(cell2mat(duration_dist(k,i)));
    %         p_ES_list(k,i) = predict_ES(cell2mat(price_dist(k,i)));
    %     end
    % end
    % 
    % for k = 1:6
    %     filename = sprintf('./Hoursly/us-east-1d/%fOD_Lb.txt', scalar(k));
    %     filename2 = sprintf('./Hoursly/us-east-1d/%fOD_ES.txt', scalar(k));
    %     fd = fopen(filename, 'w+');
    %     fd2 = fopen(filename2, 'w+');
    %     
    %     for i = 1:length(p_LB_list(k,:))
    %         for j = 1:24
    %             fprintf(fd, '%f     %d\n', [p_LB_list(k,i) i]);
    %             fprintf(fd2, '%f     %d\n', [p_ES_list(k,i) i]);
    %         end
    %     end
    % end


    LB_overestimate = zeros(length(B), 1);
    ES_diff = zeros(length(B), 1);
    %ES_underestimate = zeros(length(B), 1);

    for k = 1:length(B)
        LB_all = [];
        LB_all_pred = [];
        ES_all = [];
        ES_all_pred = [];
        ES_delta = [];
        overestimate_count = 0;
        underestimate_count = 0;
        total_LB = 0;

        for i = 1:D-window_length-1


            data = price((i+window_length)*1440+1:(i+window_length+1)*1440);
            [LB, start_pts] = find_Lb(data,B(k));
            E_price = find_ES_new(data,B(k));

            predited_LB = predict_LB_new(cell2mat(duration_dist(k,i+window_length-1)), window_length);
            predited_ES = predict_ES(cell2mat(price_dist(k,i+window_length-1)));


            for j = 1:length(LB)

                total_LB = total_LB + 1;
                if LB(j) < predited_LB
                    overestimate_count = overestimate_count + 1;
                    if j < length(LB) % if we still have more LB
                        new_start = start_pts(j+1)+(i+window_length)*1440-(7*1440);
                        new_end = start_pts(j+1)+(i+window_length)*1440;
                        look_back_data = price(new_start:new_end);
                        new_duration = [];
                        new_ES = [];

                        for n = 1:7
                            new_duration = [new_duration find_Lb(look_back_data((n-1)*1440+1:n*1440), B(k))];
                            new_ES = [new_ES find_ES_new(look_back_data((n-1)*1440+1:n*1440), B(k))];
                        end
                        predited_LB = predict_LB_new(new_duration, window_length);
                        predited_ES = predict_ES(new_ES);
                    end
                end


    %             if E_price(j) > predited_ES
    %                 underestimate_count = underestimate_count + 1;
    %             end
                if E_price(j) ~= 0 && predited_LB > 60
                    ES_delta = [ES_delta (abs(E_price(j)-predited_ES)/E_price(j))];
                end

                LB_all = [LB_all LB(j)];
                LB_all_pred = [LB_all_pred predited_LB];
                ES_all = [ES_all E_price(j)];
                ES_all_pred = [ES_all_pred predited_ES];
            end
        end
        LB_overestimate(k) = overestimate_count / total_LB;


        if length(ES_delta) == 0
            ES_diff(k) = 0;
        else
    %         ES_dot_product = ES_delta.*LB_all;
    %         ES_foo = ES_dot_product / sum(LB_all);
            ES_diff(k) = mean(ES_delta);
        end
        %ES_underestimate(k) = underestimate_count / total_LB;

        %------------------- plot LB figures
%         figure;
%         plot(LB_all);
%         hold on
%         plot(LB_all_pred);
%         hold off
%         legend('LB all', 'LB all pred');
        %saveas(gcf, sprintf('%s/BID=%f.png', dst_path,B(k)));

        %------------------- plot ES figures
    %     figure;
    %     plot(ES_all);
    %     hold on
    %     plot(ES_all_pred);
    %     hold off
    %     legend('ES all', 'ES all pred');
    %     saveas(gcf, sprintf('%s/BID=%f_ES.png', dst_path,B(k)));

    end

    %-------------- plot spot trace
    % figure;
    % plot(price);
    % saveas(gcf,sprintf('%s/spot_price_trace.png', dst_path));



end

