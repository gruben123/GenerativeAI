#include <iostream>

bool checkPrimeCPU(long long num){
  if(num<=1) return false;
  if(num==2) return true;
  if(num%2==0) return false;

  for(long long i=3;i*i<=num;i+=2){
    if(num%i==0) return false;
  }

  return true;
}

void main(){
    std::cout<<"Is the number 27 a prime number? "<<checkPrimeCPU(27)<<std::endl;
}