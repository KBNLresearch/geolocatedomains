
## Processing steps


### Split domain file

Split domain file in 6 smaller files (1 million records each)

```
split -l 1000000 -d 2019-05-21_all_domains_NL.txt domains-nl
```

### Run geolocation script

Process files with [this script](https://github.com/KBNLresearch/geolocatedomains/blob/master/scripts/geolocatedomains.py), running on virtual machine in SURFsara [HPC Cloud](https://doc.hpccloud.surfsara.nl/)

### Spatial join with province layer 

Import resulting files in [QGIS](https://www.qgis.org/).

For each location, establish corresponding province using [Dutch Province polygons layer](https://www.nationaalgeoregister.nl/geonetwork/srv/dut/catalog.search#/metadata/e73b01f6-28c7-4bb7-a782-e877e8113e2c). According to description, provinces file is suitable for map scales range 1:750,000 - 1:1,000,000, which implies spatial accuracy of about 1 km. In QGIS: *Data Management Tools*, *Join Attributes by Location ...* and then export resulting layer as CSV. Repeat for each of the 6 files.

### Combine CSVs

Combine the 6 output CSV files using (head command writes header line of 1st file to output file; subsequent tail commands append all lines *except header line* from all files):

```
head -1 ~/kb/geolocation-nldomain/qgis/domains-nl00-join-prov.csv > domains-nl-join-prov.csv; tail -n +2 -q ~/kb/geolocation-nldomain/qgis/domains-nl0?-join-prov.csv >> domains-nl-join-prov.csv
```

### Install Python Pandas

```
sudo apt-get install python3-pandas
sudo python3 -m pip install markdown
sudo python3 -m pip install tabulate
sudo python3 -m pip install matplotlib
```

