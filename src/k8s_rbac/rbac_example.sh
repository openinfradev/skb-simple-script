#!/bin/bash
SCRIPT_HOME=$(pwd)

# ClusterID ex, c01234567
ENV="c01234567"

NS=("app1" "app2" "app3")
ROLES=("admin" "view")

for ns in ${NS[@]}
do
  $SCRIPT_HOME/role_maker.sh $ns
  for role in ${ROLES[@]}
  do
    $SCRIPT_HOME/rolebinding_maker.sh $ENV $ns $role
  done
done
