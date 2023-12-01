#!/bin/bash
SCRIPT_HOME=$(pwd)

NS=("app1" "app2" "app3")
ROLES=("admin" "view")

for ns in ${NS[@]}
do
  $SCRIPT_HOME/role_maker.sh $ns
  for role in ${ROLES[@]}
  do
    $SCRIPT_HOME/rolebinding_maker.sh $ns $role
  done
done
