export function apiFetch(input:RequestInfo|URL,init:RequestInit={}){
  const token=typeof window!=="undefined"?window.sessionStorage.getItem("finintel-api-key"):null;
  const headers=new Headers(init.headers);
  if(token)headers.set("Authorization",`Bearer ${token}`);
  return fetch(input,{...init,headers});
}
export function websocketProtocols(){
  const token=typeof window!=="undefined"?window.sessionStorage.getItem("finintel-api-key"):null;
  return ["finintel.events.v1",...(token?[`bearer.${token}`]:[])];
}
