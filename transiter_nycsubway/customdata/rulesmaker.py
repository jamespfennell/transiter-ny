import csv




def _csv_iterator(csv_file_path):
    with open(csv_file_path) as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            yield row

lines = []
lines.append('stop_id,direction_name')
for row in _csv_iterator('direction_name_rules_basic.csv'):
    if row['direction_id'] == '0':
        direction = 'S'
    else:
        direction = 'N'
    lines.append('{}{},"{}"'.format(row['stop_id'], direction, row['direction_name']))
    #print(row)


with open('direction_name_rules_basic_2.csv', 'w') as f:
    f.write('\n'.join(lines))

lines = []
lines.append('stop_id,track,direction_name')
for row in _csv_iterator('direction_name_rules_with_track.csv'):
    if row['direction_id'] == '0':
        direction = 'S'
    else:
        direction = 'N'
    lines.append('{}{},{},"{}"'.format(row['stop_id'], direction, row['track'], row['direction_name']))
    # print(row)

with open('direction_name_rules_with_track_2.csv', 'w') as f:
    f.write('\n'.join(lines))




