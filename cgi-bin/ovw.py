import funct
import configparser
import json
import os
import cgi

path_config = "haproxy-webintarface.config"
config = configparser.ConfigParser()
config.read(path_config)

time_zone = config.get('main', 'time_zone')
cgi_path = config.get('main', 'cgi_path')
fullpath = config.get('main', 'fullpath')
stats_port= config.get('haproxy', 'stats_port')
haproxy_config_path  = config.get('haproxy', 'haproxy_config_path')
status_command = config.get('haproxy', 'status_command')
hap_configs_dir = config.get('configs', 'haproxy_save_configs_dir')
form = cgi.FieldStorage()

def get_overview():
	USERS =  cgi_path + '/users'

	try:
		with open(USERS, "r") as user:
			pass
	except IOError:
		print("Can't load users DB")
	
	print('<table class="overview">')

	if funct.is_admin():
		print('<tr class="overviewHead">'
				'<td class="padding10">Login</td>'
				'<td>Group</td>'
				'<td class="padding10">'
					'Role'
				'</td><td style="width: 200px;">'
					'<span class="add-button">'
						'<a href="#"  title="Show all users" id="show-all-users" style="color: #fff">'
							'Show all'
						'</a>'
					'</span>'
				'</td>'
			'</tr>')

		i = 0
		style = ""
		for f in open(USERS, 'r'):
			i = i + 1
			users = json.loads(f)
			if i is 4:
				style = 'style="display: none;" class="show-users"'
			print('<tr ' + style + '><td class="padding10 first-collumn">' + users['login'] +'</td><td class="second-collumn">')
			print(users['group']+'</td><td>')
			print(users['role'])
			print('</td><td></td></tr>')
		print('</table>')
		
	print('<table class="overview">'
		'<tr class="overviewHead">'
			'<td class="padding10">Server</td>'
			'<td class="padding10">'
				'HAproxy status'
			'</td>'
			'<td class="padding10">'
				'Action'
			'</td>'
			'<td>'
				'Last edit'
			'</td>'
		'</tr>')
		
	listhap = funct.get_dick_after_permit()

	commands = [ "ps -Af |grep [h]aproxy |wc -l" ]
	commands1 = [ "ls -l %s |awk '{ print $6\" \"$7\" \"$8}'" % haproxy_config_path ]

	for i in sorted(listhap):
		print('<tr><td class="padding10 first-collumn"><a href="#%s" title="Go to %s status" style="color: #000">%s</a></td><td  class="second-collumn">' % (i, i, i))
		funct.ssh_command(listhap.get(i), commands, server_status="1")
		print('</td><td>')
		if funct.is_admin():
			print('<a id="%s" title="Start HAproxy service" onclick = "if (! confirm(\'Start service?\')) return false;"><img src=/image/pic/start.png alt="start" class="icon"></a>' % listhap.get(i))
			print('<a id="%s" title="Stop HAproxy service" onclick = "if (! confirm(\'Stop service?\')) return false;"><img src=/image/pic/stop.png alt="start" class="icon"></a>' % listhap.get(i))
			print('<a id="%s" title="Restart HAproxy service" onclick = "if (! confirm(\'Restart service?\')) return false;"><img src=/image/pic/update.png alt="restart" class="icon"></a>' % listhap.get(i))
		print('<a href="/cgi-bin/configshow.py?serv=%s&open=open#conf"  title="Show config"><img src=/image/pic/show.png alt="show" class="icon"></a>' % listhap.get(i))
		print('<a href="/cgi-bin/config.py?serv=%s&open=open#conf"  title="Edit config"><img src=/image/pic/edit.png alt="edit" class="icon"></a>' % listhap.get(i))
		print('<a href="/cgi-bin/diff.py?serv=%s&open=open#diff"  title="Compare config"><img src=/image/pic/compare.png alt="compare" class="icon"></a>' % listhap.get(i))
		print('<a href="/cgi-bin/map.py?serv=%s&open=open#map"  title="Map listen/frontend/backend"><img src=/image/pic/map.png alt="map" class="icon"></a>' % listhap.get(i))
		print('</td><td>')
		funct.ssh_command(listhap.get(i), commands1)
		print('</td><td></td></tr>')

	print('</table><table class="overview"><tr class="overviewHead">'
			'<td class="padding10">Server</td>'
			'<td class="padding10">'
				'HAproxy info'
			'</td>'
			'<td>'
				'Server status'
			'</td>'
		'</tr>')
	print('</td></tr>')
	commands = [ "cat " + haproxy_config_path + " |grep -E '^listen|^backend|^frontend' |grep -v stats |wc -l",  
				"uname -smor", 
				"haproxy -v |head -1", 
				status_command + "|grep Active | sed 's/^[ \t]*//'" ]
	commands1 =  [ "top -u haproxy -b -n 1" ]
	for i in sorted(listhap):
		print('<tr><td class="overviewTr first-collumn"><a name="'+i+'"></a><h3 title="IP ' + listhap.get(i) + '">' + i + ':</h3></td>')
		print('<td class="overviewTd"><span>Total listen/frontend/backend:</span><pre>')
		funct.ssh_command(listhap.get(i), commands)
		print('</pre></td><td class="overviewTd"><pre>')
		funct.ssh_command(listhap.get(i), commands1)
		print('</pre></td></tr>')
		
	print('<tr></table>')
	
def get_map(serv):
	from datetime import datetime
	from pytz import timezone
	import networkx as nx
	import matplotlib
	matplotlib.use('Agg')
	import matplotlib.pyplot as plt
	
	fmt = "%Y-%m-%d.%H:%M:%S"
	now_utc = datetime.now(timezone(time_zone))
	cfg = hap_configs_dir + serv + "-" + now_utc.strftime(fmt) + ".cfg"
	
	print('<center>')
	print("<h3>Map from %s</h3><br />" % serv)
	
	G = nx.DiGraph()
	
	funct.get_config(serv, cfg)	
	conf = open(cfg, "r")
	
	node = ""
	line_new2 = [1,""]
	i = 1200
	k = 1200
	j = 0
	m = 0
	for line in conf:
		if "listen" in line or "frontend" in line:
			if "stats" not in line:				
				node = line
				i = i - 500	
		if line.find("backend") == 0: 
			node = line
			i = i - 500	
			G.add_node(node,pos=(k,i),label_pos=(k,i+150))
		
		if "bind" in line:
			bind = line.split(":")
			if stats_port not in bind[1]:
				bind[1] = bind[1].strip(' ')
				bind = bind[1].split("crt")
				node = node.strip(' \t\n\r')
				node = node + ":" + bind[0]
				G.add_node(node,pos=(k,i),label_pos=(k,i+150))

		if "server " in line or "use_backend" in line or "default_backend" in line and "stats" not in line:
			if "timeout" not in line and "default-server" not in line and "#use_backend" not in line and "stats" not in line:
				i = i - 300
				j = j + 1				
				if "check" in line:
					line_new = line.split("check")
				else:
					line_new = line.split("if ")
				if "server" in line:
					line_new1 = line_new[0].split("server")
					line_new[0] = line_new1[1]	
					line_new2 = line_new[0].split(":")
					line_new[0] = line_new2[0]					
				
				line_new[0] = line_new[0].strip(' \t\n\r')
				line_new2[1] = line_new2[1].strip(' \t\n\r')

				if j % 2 == 0:
					G.add_node(line_new[0],pos=(k+250,i-350),label_pos=(k+225,i-100))
				else:
					G.add_node(line_new[0],pos=(k-250,i-50),label_pos=(k-225,i+180))

				if line_new2[1] != "":	
					G.add_edge(node, line_new[0], port=line_new2[1])
				else:
					G.add_edge(node,line_new[0])

	os.system("/bin/rm -f " + cfg)	
	os.chdir(cgi_path)

	pos=nx.get_node_attributes(G,'pos')
	pos_label=nx.get_node_attributes(G,'label_pos')
	edge_labels = nx.get_edge_attributes(G,'port')
	
	try:
		plt.figure(10,figsize=(9.5,15))
		nx.draw(G, pos, with_labels=False, font_weight='bold', width=3, alpha=0.1,linewidths=5)	
		nx.draw_networkx_nodes(G,pos, node_color="skyblue", node_size=100, alpha=0.8, node_shape="p")
		nx.draw_networkx_labels(G,pos=pos_label, alpha=1, font_color="green", font_size=10)
		nx.draw_networkx_edges(G,pos, width=0.5,alpha=0.5, edge_color="#5D9CEB",arrows=False)
		nx.draw_networkx_edge_labels(G, pos,label_pos=0.5,font_color="blue", labels=edge_labels, font_size=8)
		
		plt.savefig("map.png")
		plt.show()
	except Exception as e:
		print("!!! There was an issue, " + str(e))
		
	commands = [ "rm -f "+fullpath+"/map*.png", "mv %s/map.png %s/map%s.png" % (cgi_path, fullpath, now_utc.strftime(fmt)) ]
	funct.ssh_command("localhost", commands)
	print('<img src="/map%s.png" alt="map">' % now_utc.strftime(fmt))

def show_compare_configs(serv):
	import glob
	left = form.getvalue('left')
	right = form.getvalue('right')
	haproxy_configs_server = config.get('configs', 'haproxy_configs_server')
	
	print('<form action="diff.py#diff" method="get">')
	print('<center><h3><span style="padding: 20px;">Choose left</span><span style="padding: 110px;">Choose right</span></h3>')
	
	print('<p><select autofocus required name="left" id="left">')
	print('<option disabled selected>Choose version</option>')
	
	os.chdir(hap_configs_dir)
	
	for files in sorted(glob.glob('*.cfg')):
		ip = files.split("-")
		if serv == ip[0]:
			if left == files:
				selected = 'selected'
			else:
				selected = ''
			print('<option value="%s" %s>%s</option>' % (files, selected, files))

	print('</select>')

	print('<select autofocus required name="right" id="right">')
	print('<option disabled selected>Choose version</option>')
	
	for files in sorted(glob.glob('*.cfg')):
		ip = files.split("-")
		if serv == ip[0]:
			if right == files:
				selected = 'selected'
			else:
				selected = ''
			print('<option value="%s" %s>%s</option>' % (files, selected, files))

	print('</select>')
	print('<input type="hidden" value="%s" name="serv">' % serv)
	print('<input type="hidden" value="open" name="open">')
	print('<a class="ui-button ui-widget ui-corner-all" id="show" title="Compare" onclick="showCompare()">Show</a></p></form></center></center>')
	
def comapre_show():
	left = form.getvalue('left')
	right = form.getvalue('right')
	haproxy_configs_server = config.get('configs', 'haproxy_configs_server')
	hap_configs_dir = config.get('configs', 'haproxy_save_configs_dir')
	commands = [ 'diff -ub %s%s %s%s' % (hap_configs_dir, left, hap_configs_dir, right) ]

	funct.ssh_command(haproxy_configs_server, commands, compare="1")