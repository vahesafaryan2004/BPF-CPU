#!/bin/bash

permission_check() {
	 if [ $USER != "root" ]; then
		 echo Run script with root user
		 exit 1
	 fi
	
}

os_checker() {
	os_name="$(grep -w "NAME" /etc/os-release)" &&
	ubuntu='NAME="Ubuntu"'
	centos='NAME="CentOs Linux"'
	if [ $os_name == $ubuntu ] ;then
		os_name="ubuntu"
	elif [ $os_name= $centos ] ;then
		os_name= "centos"
	elif [ $os_name == $bagrevand ] ;then
		os_name= "bagrevand"
	else 
		os_name="Undifinded os"
		echo $os_name
		exit 2
	fi
}

required_process() { 
	if [ $os_name == "ubuntu" ]; then 
		pr_list=( "a.out" "b.out")
		#pr_list=( "kworker" "name1")
	elif [ $os_name == "centos" ]; then 
	       pr_list=("kworker" "rcu_sched" "xfsaild" "rngd" "ksoftirqd" "watchdog" )
	elif [ $os_name == "bagrevand"]; then
		pr_list=("name1" "name2")
	fi
}	 

get_req_process() { 
	./main.py $1
	if [ -f "pr_n.txt" ]; then
		rm -rf pr_n.txt 
	fi
	for i in ${pr_list[@]};do
		pr_n="$(grep -w $i one.txt)" 
		echo "$pr_n" >> pr_n.txt
	done
	req_process_pid=$(awk '{print $2}' pr_n.txt)
	req_process_name=$(awk '{print $4}' pr_n.txt)
	req_process_name_arr=()
	req_process_pid_arr=()
	for k in $req_process_name;do
		req_process_name_arr+=("$k")
	done
	for j in $req_process_pid;do
		req_process_pid_arr+=("$j")
	done
	rm -rf pr_n.txt
}

get_process_pid() { 
	p_p="$(grep -w $1 other.txt)" 
	if [ -z "$p_p" ]; then
		echo No such process name 
		exit 1
	fi
	echo "$p_p" >> p.id
	lines="$(wc -l < p.id)"
	if [ -f "p.id" ]; then
                rm -rf p_id
        fi
	p_pid=" $(awk '{print $2}' p.id)"
}

kill_proc_pids() { 
	all_process_pid=$(awk '{print $2}' one.txt)
	all_process_name=$(awk '{print $4}' one.txt)
	changed_process=()
	eq_proc_name=()
	p=0
	for k in $all_process_name;do
		for x in ${pr_list[@]};do
			proc_name=$k
			if [ "$k" == "$x" ];then
				echo $k >> xall.txt
				eq_proc_name+=$k
				p=1
				continue
			fi
		done
		if [ $p == 1 ];then
			p=0
			changed_process_name=( "${changed_process_name[@]/$proc_name}" )
			echo ${changed_process_name[@]} >> process
			continue
			echo $p >> vlaue
		else 
			changed_process_name+=("$proc_name")
		fi
		echo $p >> vlaue
				echo $k >> all.txt
	done
	echo "${changed_process_name[@]} \n" >> files	
}

set_cpu_priority() {
	p_pid_arr=()
	for k in $p_pid;do
                p_pid_arr+=("$k")
        done
	for x in ${p_pid_arr[@]};do
		taskset -cp $1 $x > /dev/null
		renice --priority 19 $x > /dev/null
	done
}

main() { 	
	permission_check
	os_checker 
	required_process
	get_req_process $3 
	kill_proc_pids
	if [ "$1" == "-nc" ];then
		get_process_pid $2
		set_cpu_priority $3
	fi
	return 10
}
main $1 $2 $3
