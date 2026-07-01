var e=Object.create,t=Object.defineProperty,n=Object.getOwnPropertyDescriptor,r=Object.getOwnPropertyNames,i=Object.getPrototypeOf,a=Object.prototype.hasOwnProperty,o=(e,t)=>()=>(t||(e((t={exports:{}}).exports,t),e=null),t.exports),s=(e,i,o,s)=>{if(i&&typeof i==`object`||typeof i==`function`)for(var c=r(i),l=0,u=c.length,d;l<u;l++)d=c[l],!a.call(e,d)&&d!==o&&t(e,d,{get:(e=>i[e]).bind(null,d),enumerable:!(s=n(i,d))||s.enumerable});return e},c=(n,r,a)=>(a=n==null?{}:e(i(n)),s(r||!n||!n.__esModule?t(a,`default`,{value:n,enumerable:!0}):a,n));(function(){let e=document.createElement(`link`).relList;if(e&&e.supports&&e.supports(`modulepreload`))return;for(let e of document.querySelectorAll(`link[rel="modulepreload"]`))n(e);new MutationObserver(e=>{for(let t of e)if(t.type===`childList`)for(let e of t.addedNodes)e.tagName===`LINK`&&e.rel===`modulepreload`&&n(e)}).observe(document,{childList:!0,subtree:!0});function t(e){let t={};return e.integrity&&(t.integrity=e.integrity),e.referrerPolicy&&(t.referrerPolicy=e.referrerPolicy),e.crossOrigin===`use-credentials`?t.credentials=`include`:e.crossOrigin===`anonymous`?t.credentials=`omit`:t.credentials=`same-origin`,t}function n(e){if(e.ep)return;e.ep=!0;let n=t(e);fetch(e.href,n)}})();var l=o(((e,t)=>{t.exports=function(){return typeof Promise==`function`&&Promise.prototype&&Promise.prototype.then}})),u=o((e=>{var t,n=[0,26,44,70,100,134,172,196,242,292,346,404,466,532,581,655,733,815,901,991,1085,1156,1258,1364,1474,1588,1706,1828,1921,2051,2185,2323,2465,2611,2761,2876,3034,3196,3362,3532,3706];e.getSymbolSize=function(e){if(!e)throw Error(`"version" cannot be null or undefined`);if(e<1||e>40)throw Error(`"version" should be in range from 1 to 40`);return e*4+17},e.getSymbolTotalCodewords=function(e){return n[e]},e.getBCHDigit=function(e){let t=0;for(;e!==0;)t++,e>>>=1;return t},e.setToSJISFunction=function(e){if(typeof e!=`function`)throw Error(`"toSJISFunc" is not a valid function.`);t=e},e.isKanjiModeEnabled=function(){return t!==void 0},e.toSJIS=function(e){return t(e)}})),d=o((e=>{e.L={bit:1},e.M={bit:0},e.Q={bit:3},e.H={bit:2};function t(t){if(typeof t!=`string`)throw Error(`Param is not a string`);switch(t.toLowerCase()){case`l`:case`low`:return e.L;case`m`:case`medium`:return e.M;case`q`:case`quartile`:return e.Q;case`h`:case`high`:return e.H;default:throw Error(`Unknown EC Level: `+t)}}e.isValid=function(e){return e&&e.bit!==void 0&&e.bit>=0&&e.bit<4},e.from=function(n,r){if(e.isValid(n))return n;try{return t(n)}catch{return r}}})),f=o(((e,t)=>{function n(){this.buffer=[],this.length=0}n.prototype={get:function(e){let t=Math.floor(e/8);return(this.buffer[t]>>>7-e%8&1)==1},put:function(e,t){for(let n=0;n<t;n++)this.putBit((e>>>t-n-1&1)==1)},getLengthInBits:function(){return this.length},putBit:function(e){let t=Math.floor(this.length/8);this.buffer.length<=t&&this.buffer.push(0),e&&(this.buffer[t]|=128>>>this.length%8),this.length++}},t.exports=n})),p=o(((e,t)=>{function n(e){if(!e||e<1)throw Error(`BitMatrix size must be defined and greater than 0`);this.size=e,this.data=new Uint8Array(e*e),this.reservedBit=new Uint8Array(e*e)}n.prototype.set=function(e,t,n,r){let i=e*this.size+t;this.data[i]=n,r&&(this.reservedBit[i]=!0)},n.prototype.get=function(e,t){return this.data[e*this.size+t]},n.prototype.xor=function(e,t,n){this.data[e*this.size+t]^=n},n.prototype.isReserved=function(e,t){return this.reservedBit[e*this.size+t]},t.exports=n})),m=o((e=>{var t=u().getSymbolSize;e.getRowColCoords=function(e){if(e===1)return[];let n=Math.floor(e/7)+2,r=t(e),i=r===145?26:Math.ceil((r-13)/(2*n-2))*2,a=[r-7];for(let e=1;e<n-1;e++)a[e]=a[e-1]-i;return a.push(6),a.reverse()},e.getPositions=function(t){let n=[],r=e.getRowColCoords(t),i=r.length;for(let e=0;e<i;e++)for(let t=0;t<i;t++)e===0&&t===0||e===0&&t===i-1||e===i-1&&t===0||n.push([r[e],r[t]]);return n}})),h=o((e=>{var t=u().getSymbolSize,n=7;e.getPositions=function(e){let r=t(e);return[[0,0],[r-n,0],[0,r-n]]}})),g=o((e=>{e.Patterns={PATTERN000:0,PATTERN001:1,PATTERN010:2,PATTERN011:3,PATTERN100:4,PATTERN101:5,PATTERN110:6,PATTERN111:7};var t={N1:3,N2:3,N3:40,N4:10};e.isValid=function(e){return e!=null&&e!==``&&!isNaN(e)&&e>=0&&e<=7},e.from=function(t){return e.isValid(t)?parseInt(t,10):void 0},e.getPenaltyN1=function(e){let n=e.size,r=0,i=0,a=0,o=null,s=null;for(let c=0;c<n;c++){i=a=0,o=s=null;for(let l=0;l<n;l++){let n=e.get(c,l);n===o?i++:(i>=5&&(r+=t.N1+(i-5)),o=n,i=1),n=e.get(l,c),n===s?a++:(a>=5&&(r+=t.N1+(a-5)),s=n,a=1)}i>=5&&(r+=t.N1+(i-5)),a>=5&&(r+=t.N1+(a-5))}return r},e.getPenaltyN2=function(e){let n=e.size,r=0;for(let t=0;t<n-1;t++)for(let i=0;i<n-1;i++){let n=e.get(t,i)+e.get(t,i+1)+e.get(t+1,i)+e.get(t+1,i+1);(n===4||n===0)&&r++}return r*t.N2},e.getPenaltyN3=function(e){let n=e.size,r=0,i=0,a=0;for(let t=0;t<n;t++){i=a=0;for(let o=0;o<n;o++)i=i<<1&2047|e.get(t,o),o>=10&&(i===1488||i===93)&&r++,a=a<<1&2047|e.get(o,t),o>=10&&(a===1488||a===93)&&r++}return r*t.N3},e.getPenaltyN4=function(e){let n=0,r=e.data.length;for(let t=0;t<r;t++)n+=e.data[t];return Math.abs(Math.ceil(n*100/r/5)-10)*t.N4};function n(t,n,r){switch(t){case e.Patterns.PATTERN000:return(n+r)%2==0;case e.Patterns.PATTERN001:return n%2==0;case e.Patterns.PATTERN010:return r%3==0;case e.Patterns.PATTERN011:return(n+r)%3==0;case e.Patterns.PATTERN100:return(Math.floor(n/2)+Math.floor(r/3))%2==0;case e.Patterns.PATTERN101:return n*r%2+n*r%3==0;case e.Patterns.PATTERN110:return(n*r%2+n*r%3)%2==0;case e.Patterns.PATTERN111:return(n*r%3+(n+r)%2)%2==0;default:throw Error(`bad maskPattern:`+t)}}e.applyMask=function(e,t){let r=t.size;for(let i=0;i<r;i++)for(let a=0;a<r;a++)t.isReserved(a,i)||t.xor(a,i,n(e,a,i))},e.getBestMask=function(t,n){let r=Object.keys(e.Patterns).length,i=0,a=1/0;for(let o=0;o<r;o++){n(o),e.applyMask(o,t);let r=e.getPenaltyN1(t)+e.getPenaltyN2(t)+e.getPenaltyN3(t)+e.getPenaltyN4(t);e.applyMask(o,t),r<a&&(a=r,i=o)}return i}})),_=o((e=>{var t=d(),n=[1,1,1,1,1,1,1,1,1,1,2,2,1,2,2,4,1,2,4,4,2,4,4,4,2,4,6,5,2,4,6,6,2,5,8,8,4,5,8,8,4,5,8,11,4,8,10,11,4,9,12,16,4,9,16,16,6,10,12,18,6,10,17,16,6,11,16,19,6,13,18,21,7,14,21,25,8,16,20,25,8,17,23,25,9,17,23,34,9,18,25,30,10,20,27,32,12,21,29,35,12,23,34,37,12,25,34,40,13,26,35,42,14,28,38,45,15,29,40,48,16,31,43,51,17,33,45,54,18,35,48,57,19,37,51,60,19,38,53,63,20,40,56,66,21,43,59,70,22,45,62,74,24,47,65,77,25,49,68,81],r=[7,10,13,17,10,16,22,28,15,26,36,44,20,36,52,64,26,48,72,88,36,64,96,112,40,72,108,130,48,88,132,156,60,110,160,192,72,130,192,224,80,150,224,264,96,176,260,308,104,198,288,352,120,216,320,384,132,240,360,432,144,280,408,480,168,308,448,532,180,338,504,588,196,364,546,650,224,416,600,700,224,442,644,750,252,476,690,816,270,504,750,900,300,560,810,960,312,588,870,1050,336,644,952,1110,360,700,1020,1200,390,728,1050,1260,420,784,1140,1350,450,812,1200,1440,480,868,1290,1530,510,924,1350,1620,540,980,1440,1710,570,1036,1530,1800,570,1064,1590,1890,600,1120,1680,1980,630,1204,1770,2100,660,1260,1860,2220,720,1316,1950,2310,750,1372,2040,2430];e.getBlocksCount=function(e,r){switch(r){case t.L:return n[(e-1)*4+0];case t.M:return n[(e-1)*4+1];case t.Q:return n[(e-1)*4+2];case t.H:return n[(e-1)*4+3];default:return}},e.getTotalCodewordsCount=function(e,n){switch(n){case t.L:return r[(e-1)*4+0];case t.M:return r[(e-1)*4+1];case t.Q:return r[(e-1)*4+2];case t.H:return r[(e-1)*4+3];default:return}}})),v=o((e=>{var t=new Uint8Array(512),n=new Uint8Array(256);(function(){let e=1;for(let r=0;r<255;r++)t[r]=e,n[e]=r,e<<=1,e&256&&(e^=285);for(let e=255;e<512;e++)t[e]=t[e-255]})(),e.log=function(e){if(e<1)throw Error(`log(`+e+`)`);return n[e]},e.exp=function(e){return t[e]},e.mul=function(e,r){return e===0||r===0?0:t[n[e]+n[r]]}})),y=o((e=>{var t=v();e.mul=function(e,n){let r=new Uint8Array(e.length+n.length-1);for(let i=0;i<e.length;i++)for(let a=0;a<n.length;a++)r[i+a]^=t.mul(e[i],n[a]);return r},e.mod=function(e,n){let r=new Uint8Array(e);for(;r.length-n.length>=0;){let e=r[0];for(let i=0;i<n.length;i++)r[i]^=t.mul(n[i],e);let i=0;for(;i<r.length&&r[i]===0;)i++;r=r.slice(i)}return r},e.generateECPolynomial=function(n){let r=new Uint8Array([1]);for(let i=0;i<n;i++)r=e.mul(r,new Uint8Array([1,t.exp(i)]));return r}})),b=o(((e,t)=>{var n=y();function r(e){this.genPoly=void 0,this.degree=e,this.degree&&this.initialize(this.degree)}r.prototype.initialize=function(e){this.degree=e,this.genPoly=n.generateECPolynomial(this.degree)},r.prototype.encode=function(e){if(!this.genPoly)throw Error(`Encoder not initialized`);let t=new Uint8Array(e.length+this.degree);t.set(e);let r=n.mod(t,this.genPoly),i=this.degree-r.length;if(i>0){let e=new Uint8Array(this.degree);return e.set(r,i),e}return r},t.exports=r})),x=o((e=>{e.isValid=function(e){return!isNaN(e)&&e>=1&&e<=40}})),S=o((e=>{var t=`[0-9]+`,n=`[A-Z $%*+\\-./:]+`,r=`(?:[u3000-u303F]|[u3040-u309F]|[u30A0-u30FF]|[uFF00-uFFEF]|[u4E00-u9FAF]|[u2605-u2606]|[u2190-u2195]|u203B|[u2010u2015u2018u2019u2025u2026u201Cu201Du2225u2260]|[u0391-u0451]|[u00A7u00A8u00B1u00B4u00D7u00F7])+`;r=r.replace(/u/g,`\\u`);var i=`(?:(?![A-Z0-9 $%*+\\-./:]|`+r+`)(?:.|[\r
]))+`;e.KANJI=new RegExp(r,`g`),e.BYTE_KANJI=RegExp(`[^A-Z0-9 $%*+\\-./:]+`,`g`),e.BYTE=new RegExp(i,`g`),e.NUMERIC=new RegExp(t,`g`),e.ALPHANUMERIC=new RegExp(n,`g`);var a=RegExp(`^`+r+`$`),o=RegExp(`^[0-9]+$`),s=RegExp(`^[A-Z0-9 $%*+\\-./:]+$`);e.testKanji=function(e){return a.test(e)},e.testNumeric=function(e){return o.test(e)},e.testAlphanumeric=function(e){return s.test(e)}})),C=o((e=>{var t=x(),n=S();e.NUMERIC={id:`Numeric`,bit:1,ccBits:[10,12,14]},e.ALPHANUMERIC={id:`Alphanumeric`,bit:2,ccBits:[9,11,13]},e.BYTE={id:`Byte`,bit:4,ccBits:[8,16,16]},e.KANJI={id:`Kanji`,bit:8,ccBits:[8,10,12]},e.MIXED={bit:-1},e.getCharCountIndicator=function(e,n){if(!e.ccBits)throw Error(`Invalid mode: `+e);if(!t.isValid(n))throw Error(`Invalid version: `+n);return n>=1&&n<10?e.ccBits[0]:n<27?e.ccBits[1]:e.ccBits[2]},e.getBestModeForData=function(t){return n.testNumeric(t)?e.NUMERIC:n.testAlphanumeric(t)?e.ALPHANUMERIC:n.testKanji(t)?e.KANJI:e.BYTE},e.toString=function(e){if(e&&e.id)return e.id;throw Error(`Invalid mode`)},e.isValid=function(e){return e&&e.bit&&e.ccBits};function r(t){if(typeof t!=`string`)throw Error(`Param is not a string`);switch(t.toLowerCase()){case`numeric`:return e.NUMERIC;case`alphanumeric`:return e.ALPHANUMERIC;case`kanji`:return e.KANJI;case`byte`:return e.BYTE;default:throw Error(`Unknown mode: `+t)}}e.from=function(t,n){if(e.isValid(t))return t;try{return r(t)}catch{return n}}})),w=o((e=>{var t=u(),n=_(),r=d(),i=C(),a=x(),o=7973,s=t.getBCHDigit(o);function c(t,n,r){for(let i=1;i<=40;i++)if(n<=e.getCapacity(i,r,t))return i}function l(e,t){return i.getCharCountIndicator(e,t)+4}function f(e,t){let n=0;return e.forEach(function(e){let r=l(e.mode,t);n+=r+e.getBitsLength()}),n}function p(t,n){for(let r=1;r<=40;r++)if(f(t,r)<=e.getCapacity(r,n,i.MIXED))return r}e.from=function(e,t){return a.isValid(e)?parseInt(e,10):t},e.getCapacity=function(e,r,o){if(!a.isValid(e))throw Error(`Invalid QR Code version`);o===void 0&&(o=i.BYTE);let s=(t.getSymbolTotalCodewords(e)-n.getTotalCodewordsCount(e,r))*8;if(o===i.MIXED)return s;let c=s-l(o,e);switch(o){case i.NUMERIC:return Math.floor(c/10*3);case i.ALPHANUMERIC:return Math.floor(c/11*2);case i.KANJI:return Math.floor(c/13);case i.BYTE:default:return Math.floor(c/8)}},e.getBestVersionForData=function(e,t){let n,i=r.from(t,r.M);if(Array.isArray(e)){if(e.length>1)return p(e,i);if(e.length===0)return 1;n=e[0]}else n=e;return c(n.mode,n.getLength(),i)},e.getEncodedBits=function(e){if(!a.isValid(e)||e<7)throw Error(`Invalid QR Code version`);let n=e<<12;for(;t.getBCHDigit(n)-s>=0;)n^=o<<t.getBCHDigit(n)-s;return e<<12|n}})),ee=o((e=>{var t=u(),n=1335,r=21522,i=t.getBCHDigit(n);e.getEncodedBits=function(e,a){let o=e.bit<<3|a,s=o<<10;for(;t.getBCHDigit(s)-i>=0;)s^=n<<t.getBCHDigit(s)-i;return(o<<10|s)^r}})),te=o(((e,t)=>{var n=C();function r(e){this.mode=n.NUMERIC,this.data=e.toString()}r.getBitsLength=function(e){return 10*Math.floor(e/3)+(e%3?e%3*3+1:0)},r.prototype.getLength=function(){return this.data.length},r.prototype.getBitsLength=function(){return r.getBitsLength(this.data.length)},r.prototype.write=function(e){let t,n,r;for(t=0;t+3<=this.data.length;t+=3)n=this.data.substr(t,3),r=parseInt(n,10),e.put(r,10);let i=this.data.length-t;i>0&&(n=this.data.substr(t),r=parseInt(n,10),e.put(r,i*3+1))},t.exports=r})),T=o(((e,t)=>{var n=C(),r=`0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ $%*+-./:`.split(``);function i(e){this.mode=n.ALPHANUMERIC,this.data=e}i.getBitsLength=function(e){return 11*Math.floor(e/2)+e%2*6},i.prototype.getLength=function(){return this.data.length},i.prototype.getBitsLength=function(){return i.getBitsLength(this.data.length)},i.prototype.write=function(e){let t;for(t=0;t+2<=this.data.length;t+=2){let n=r.indexOf(this.data[t])*45;n+=r.indexOf(this.data[t+1]),e.put(n,11)}this.data.length%2&&e.put(r.indexOf(this.data[t]),6)},t.exports=i})),E=o(((e,t)=>{var n=C();function r(e){this.mode=n.BYTE,typeof e==`string`?this.data=new TextEncoder().encode(e):this.data=new Uint8Array(e)}r.getBitsLength=function(e){return e*8},r.prototype.getLength=function(){return this.data.length},r.prototype.getBitsLength=function(){return r.getBitsLength(this.data.length)},r.prototype.write=function(e){for(let t=0,n=this.data.length;t<n;t++)e.put(this.data[t],8)},t.exports=r})),D=o(((e,t)=>{var n=C(),r=u();function i(e){this.mode=n.KANJI,this.data=e}i.getBitsLength=function(e){return e*13},i.prototype.getLength=function(){return this.data.length},i.prototype.getBitsLength=function(){return i.getBitsLength(this.data.length)},i.prototype.write=function(e){let t;for(t=0;t<this.data.length;t++){let n=r.toSJIS(this.data[t]);if(n>=33088&&n<=40956)n-=33088;else if(n>=57408&&n<=60351)n-=49472;else throw Error(`Invalid SJIS character: `+this.data[t]+`
Make sure your charset is UTF-8`);n=(n>>>8&255)*192+(n&255),e.put(n,13)}},t.exports=i})),O=o(((e,t)=>{var n={single_source_shortest_paths:function(e,t,r){var i={},a={};a[t]=0;var o=n.PriorityQueue.make();o.push(t,0);for(var s,c,l,u,d,f,p,m,h;!o.empty();)for(l in s=o.pop(),c=s.value,u=s.cost,d=e[c]||{},d)d.hasOwnProperty(l)&&(f=d[l],p=u+f,m=a[l],h=a[l]===void 0,(h||m>p)&&(a[l]=p,o.push(l,p),i[l]=c));if(r!==void 0&&a[r]===void 0){var g=[`Could not find a path from `,t,` to `,r,`.`].join(``);throw Error(g)}return i},extract_shortest_path_from_predecessor_list:function(e,t){for(var n=[],r=t;r;)n.push(r),e[r],r=e[r];return n.reverse(),n},find_path:function(e,t,r){var i=n.single_source_shortest_paths(e,t,r);return n.extract_shortest_path_from_predecessor_list(i,r)},PriorityQueue:{make:function(e){var t=n.PriorityQueue,r={},i;for(i in e||={},t)t.hasOwnProperty(i)&&(r[i]=t[i]);return r.queue=[],r.sorter=e.sorter||t.default_sorter,r},default_sorter:function(e,t){return e.cost-t.cost},push:function(e,t){var n={value:e,cost:t};this.queue.push(n),this.queue.sort(this.sorter)},pop:function(){return this.queue.shift()},empty:function(){return this.queue.length===0}}};t!==void 0&&(t.exports=n)})),ne=o((e=>{var t=C(),n=te(),r=T(),i=E(),a=D(),o=S(),s=u(),c=O();function l(e){return unescape(encodeURIComponent(e)).length}function d(e,t,n){let r=[],i;for(;(i=e.exec(n))!==null;)r.push({data:i[0],index:i.index,mode:t,length:i[0].length});return r}function f(e){let n=d(o.NUMERIC,t.NUMERIC,e),r=d(o.ALPHANUMERIC,t.ALPHANUMERIC,e),i,a;return s.isKanjiModeEnabled()?(i=d(o.BYTE,t.BYTE,e),a=d(o.KANJI,t.KANJI,e)):(i=d(o.BYTE_KANJI,t.BYTE,e),a=[]),n.concat(r,i,a).sort(function(e,t){return e.index-t.index}).map(function(e){return{data:e.data,mode:e.mode,length:e.length}})}function p(e,o){switch(o){case t.NUMERIC:return n.getBitsLength(e);case t.ALPHANUMERIC:return r.getBitsLength(e);case t.KANJI:return a.getBitsLength(e);case t.BYTE:return i.getBitsLength(e)}}function m(e){return e.reduce(function(e,t){let n=e.length-1>=0?e[e.length-1]:null;return n&&n.mode===t.mode?(e[e.length-1].data+=t.data,e):(e.push(t),e)},[])}function h(e){let n=[];for(let r=0;r<e.length;r++){let i=e[r];switch(i.mode){case t.NUMERIC:n.push([i,{data:i.data,mode:t.ALPHANUMERIC,length:i.length},{data:i.data,mode:t.BYTE,length:i.length}]);break;case t.ALPHANUMERIC:n.push([i,{data:i.data,mode:t.BYTE,length:i.length}]);break;case t.KANJI:n.push([i,{data:i.data,mode:t.BYTE,length:l(i.data)}]);break;case t.BYTE:n.push([{data:i.data,mode:t.BYTE,length:l(i.data)}])}}return n}function g(e,n){let r={},i={start:{}},a=[`start`];for(let o=0;o<e.length;o++){let s=e[o],c=[];for(let e=0;e<s.length;e++){let l=s[e],u=``+o+e;c.push(u),r[u]={node:l,lastCount:0},i[u]={};for(let e=0;e<a.length;e++){let o=a[e];r[o]&&r[o].node.mode===l.mode?(i[o][u]=p(r[o].lastCount+l.length,l.mode)-p(r[o].lastCount,l.mode),r[o].lastCount+=l.length):(r[o]&&(r[o].lastCount=l.length),i[o][u]=p(l.length,l.mode)+4+t.getCharCountIndicator(l.mode,n))}}a=c}for(let e=0;e<a.length;e++)i[a[e]].end=0;return{map:i,table:r}}function _(e,o){let c,l=t.getBestModeForData(e);if(c=t.from(o,l),c!==t.BYTE&&c.bit<l.bit)throw Error(`"`+e+`" cannot be encoded with mode `+t.toString(c)+`.
 Suggested mode is: `+t.toString(l));switch(c===t.KANJI&&!s.isKanjiModeEnabled()&&(c=t.BYTE),c){case t.NUMERIC:return new n(e);case t.ALPHANUMERIC:return new r(e);case t.KANJI:return new a(e);case t.BYTE:return new i(e)}}e.fromArray=function(e){return e.reduce(function(e,t){return typeof t==`string`?e.push(_(t,null)):t.data&&e.push(_(t.data,t.mode)),e},[])},e.fromString=function(t,n){let r=g(h(f(t,s.isKanjiModeEnabled())),n),i=c.find_path(r.map,`start`,`end`),a=[];for(let e=1;e<i.length-1;e++)a.push(r.table[i[e]].node);return e.fromArray(m(a))},e.rawSplit=function(t){return e.fromArray(f(t,s.isKanjiModeEnabled()))}})),k=o((e=>{var t=u(),n=d(),r=f(),i=p(),a=m(),o=h(),s=g(),c=_(),l=b(),v=w(),y=ee(),x=C(),S=ne();function te(e,t){let n=e.size,r=o.getPositions(t);for(let t=0;t<r.length;t++){let i=r[t][0],a=r[t][1];for(let t=-1;t<=7;t++)if(!(i+t<=-1||n<=i+t))for(let r=-1;r<=7;r++)a+r<=-1||n<=a+r||(t>=0&&t<=6&&(r===0||r===6)||r>=0&&r<=6&&(t===0||t===6)||t>=2&&t<=4&&r>=2&&r<=4?e.set(i+t,a+r,!0,!0):e.set(i+t,a+r,!1,!0))}}function T(e){let t=e.size;for(let n=8;n<t-8;n++){let t=n%2==0;e.set(n,6,t,!0),e.set(6,n,t,!0)}}function E(e,t){let n=a.getPositions(t);for(let t=0;t<n.length;t++){let r=n[t][0],i=n[t][1];for(let t=-2;t<=2;t++)for(let n=-2;n<=2;n++)t===-2||t===2||n===-2||n===2||t===0&&n===0?e.set(r+t,i+n,!0,!0):e.set(r+t,i+n,!1,!0)}}function D(e,t){let n=e.size,r=v.getEncodedBits(t),i,a,o;for(let t=0;t<18;t++)i=Math.floor(t/3),a=t%3+n-8-3,o=(r>>t&1)==1,e.set(i,a,o,!0),e.set(a,i,o,!0)}function O(e,t,n){let r=e.size,i=y.getEncodedBits(t,n),a,o;for(a=0;a<15;a++)o=(i>>a&1)==1,a<6?e.set(a,8,o,!0):a<8?e.set(a+1,8,o,!0):e.set(r-15+a,8,o,!0),a<8?e.set(8,r-a-1,o,!0):a<9?e.set(8,15-a-1+1,o,!0):e.set(8,15-a-1,o,!0);e.set(r-8,8,1,!0)}function k(e,t){let n=e.size,r=-1,i=n-1,a=7,o=0;for(let s=n-1;s>0;s-=2)for(s===6&&s--;;){for(let n=0;n<2;n++)if(!e.isReserved(i,s-n)){let r=!1;o<t.length&&(r=(t[o]>>>a&1)==1),e.set(i,s-n,r),a--,a===-1&&(o++,a=7)}if(i+=r,i<0||n<=i){i-=r,r=-r;break}}}function A(e,n,i){let a=new r;i.forEach(function(t){a.put(t.mode.bit,4),a.put(t.getLength(),x.getCharCountIndicator(t.mode,e)),t.write(a)});let o=(t.getSymbolTotalCodewords(e)-c.getTotalCodewordsCount(e,n))*8;for(a.getLengthInBits()+4<=o&&a.put(0,4);a.getLengthInBits()%8!=0;)a.putBit(0);let s=(o-a.getLengthInBits())/8;for(let e=0;e<s;e++)a.put(e%2?17:236,8);return j(a,e,n)}function j(e,n,r){let i=t.getSymbolTotalCodewords(n),a=i-c.getTotalCodewordsCount(n,r),o=c.getBlocksCount(n,r),s=o-i%o,u=Math.floor(i/o),d=Math.floor(a/o),f=d+1,p=u-d,m=new l(p),h=0,g=Array(o),_=Array(o),v=0,y=new Uint8Array(e.buffer);for(let e=0;e<o;e++){let t=e<s?d:f;g[e]=y.slice(h,h+t),_[e]=m.encode(g[e]),h+=t,v=Math.max(v,t)}let b=new Uint8Array(i),x=0,S,C;for(S=0;S<v;S++)for(C=0;C<o;C++)S<g[C].length&&(b[x++]=g[C][S]);for(S=0;S<p;S++)for(C=0;C<o;C++)b[x++]=_[C][S];return b}function re(e,n,r,a){let o;if(Array.isArray(e))o=S.fromArray(e);else if(typeof e==`string`){let t=n;if(!t){let n=S.rawSplit(e);t=v.getBestVersionForData(n,r)}o=S.fromString(e,t||40)}else throw Error(`Invalid data`);let c=v.getBestVersionForData(o,r);if(!c)throw Error(`The amount of data is too big to be stored in a QR Code`);if(!n)n=c;else if(n<c)throw Error(`
The chosen QR Code version cannot contain this amount of data.
Minimum version required to store current data is: `+c+`.
`);let l=A(n,r,o),u=new i(t.getSymbolSize(n));return te(u,n),T(u),E(u,n),O(u,r,0),n>=7&&D(u,n),k(u,l),isNaN(a)&&(a=s.getBestMask(u,O.bind(null,u,r))),s.applyMask(a,u),O(u,r,a),{modules:u,version:n,errorCorrectionLevel:r,maskPattern:a,segments:o}}e.create=function(e,r){if(e===void 0||e===``)throw Error(`No input text`);let i=n.M,a,o;return r!==void 0&&(i=n.from(r.errorCorrectionLevel,n.M),a=v.from(r.version),o=s.from(r.maskPattern),r.toSJISFunc&&t.setToSJISFunction(r.toSJISFunc)),re(e,a,i,o)}})),A=o((e=>{function t(e){if(typeof e==`number`&&(e=e.toString()),typeof e!=`string`)throw Error(`Color should be defined as hex string`);let t=e.slice().replace(`#`,``).split(``);if(t.length<3||t.length===5||t.length>8)throw Error(`Invalid hex color: `+e);(t.length===3||t.length===4)&&(t=Array.prototype.concat.apply([],t.map(function(e){return[e,e]}))),t.length===6&&t.push(`F`,`F`);let n=parseInt(t.join(``),16);return{r:n>>24&255,g:n>>16&255,b:n>>8&255,a:n&255,hex:`#`+t.slice(0,6).join(``)}}e.getOptions=function(e){e||={},e.color||={};let n=e.margin===void 0||e.margin===null||e.margin<0?4:e.margin,r=e.width&&e.width>=21?e.width:void 0,i=e.scale||4;return{width:r,scale:r?4:i,margin:n,color:{dark:t(e.color.dark||`#000000ff`),light:t(e.color.light||`#ffffffff`)},type:e.type,rendererOpts:e.rendererOpts||{}}},e.getScale=function(e,t){return t.width&&t.width>=e+t.margin*2?t.width/(e+t.margin*2):t.scale},e.getImageWidth=function(t,n){let r=e.getScale(t,n);return Math.floor((t+n.margin*2)*r)},e.qrToImageData=function(t,n,r){let i=n.modules.size,a=n.modules.data,o=e.getScale(i,r),s=Math.floor((i+r.margin*2)*o),c=r.margin*o,l=[r.color.light,r.color.dark];for(let e=0;e<s;e++)for(let n=0;n<s;n++){let u=(e*s+n)*4,d=r.color.light;if(e>=c&&n>=c&&e<s-c&&n<s-c){let t=Math.floor((e-c)/o),r=Math.floor((n-c)/o);d=l[+!!a[t*i+r]]}t[u++]=d.r,t[u++]=d.g,t[u++]=d.b,t[u]=d.a}}})),j=o((e=>{var t=A();function n(e,t,n){e.clearRect(0,0,t.width,t.height),t.style||={},t.height=n,t.width=n,t.style.height=n+`px`,t.style.width=n+`px`}function r(){try{return document.createElement(`canvas`)}catch{throw Error(`You need to specify a canvas element`)}}e.render=function(e,i,a){let o=a,s=i;o===void 0&&(!i||!i.getContext)&&(o=i,i=void 0),i||(s=r()),o=t.getOptions(o);let c=t.getImageWidth(e.modules.size,o),l=s.getContext(`2d`),u=l.createImageData(c,c);return t.qrToImageData(u.data,e,o),n(l,s,c),l.putImageData(u,0,0),s},e.renderToDataURL=function(t,n,r){let i=r;i===void 0&&(!n||!n.getContext)&&(i=n,n=void 0),i||={};let a=e.render(t,n,i),o=i.type||`image/png`,s=i.rendererOpts||{};return a.toDataURL(o,s.quality)}})),re=o((e=>{var t=A();function n(e,t){let n=e.a/255,r=t+`="`+e.hex+`"`;return n<1?r+` `+t+`-opacity="`+n.toFixed(2).slice(1)+`"`:r}function r(e,t,n){let r=e+t;return n!==void 0&&(r+=` `+n),r}function i(e,t,n){let i=``,a=0,o=!1,s=0;for(let c=0;c<e.length;c++){let l=Math.floor(c%t),u=Math.floor(c/t);!l&&!o&&(o=!0),e[c]?(s++,c>0&&l>0&&e[c-1]||(i+=o?r(`M`,l+n,.5+u+n):r(`m`,a,0),a=0,o=!1),l+1<t&&e[c+1]||(i+=r(`h`,s),s=0)):a++}return i}e.render=function(e,r,a){let o=t.getOptions(r),s=e.modules.size,c=e.modules.data,l=s+o.margin*2,u=o.color.light.a?`<path `+n(o.color.light,`fill`)+` d="M0 0h`+l+`v`+l+`H0z"/>`:``,d=`<path `+n(o.color.dark,`stroke`)+` d="`+i(c,s,o.margin)+`"/>`,f=`viewBox="0 0 `+l+` `+l+`"`,p=`<svg xmlns="http://www.w3.org/2000/svg" `+(o.width?`width="`+o.width+`" height="`+o.width+`" `:``)+f+` shape-rendering="crispEdges">`+u+d+`</svg>
`;return typeof a==`function`&&a(null,p),p}})),ie=c(o((e=>{var t=l(),n=k(),r=j(),i=re();function a(e,r,i,a,o){let s=[].slice.call(arguments,1),c=s.length,l=typeof s[c-1]==`function`;if(!l&&!t())throw Error(`Callback required as last argument`);if(l){if(c<2)throw Error(`Too few arguments provided`);c===2?(o=i,i=r,r=a=void 0):c===3&&(r.getContext&&o===void 0?(o=a,a=void 0):(o=a,a=i,i=r,r=void 0))}else{if(c<1)throw Error(`Too few arguments provided`);return c===1?(i=r,r=a=void 0):c===2&&!r.getContext&&(a=i,i=r,r=void 0),new Promise(function(t,o){try{t(e(n.create(i,a),r,a))}catch(e){o(e)}})}try{let t=n.create(i,a);o(null,e(t,r,a))}catch(e){o(e)}}e.create=n.create,e.toCanvas=a.bind(null,r.render),e.toDataURL=a.bind(null,r.renderToDataURL),e.toString=a.bind(null,function(e,t,n){return i.render(e,n)})}))(),1),ae=`/api`;async function M(e,t={}){let n=await fetch(ae+e,{headers:{"Content-Type":`application/json`},...t}),r;try{r=await n.json()}catch{r={ok:!1,error:`Non-JSON response (${n.status})`}}return!n.ok&&r.ok!==!1&&(r={ok:!1,error:`HTTP ${n.status}`}),r}var N={health:()=>M(`/../health`),reset:()=>M(`/setup/reset`,{method:`POST`}),bridgeStatus:()=>M(`/bridge/status`),bridgeQR:()=>M(`/bridge/qr`),bridgeStart:()=>M(`/bridge/start`,{method:`POST`}),bridgeStop:()=>M(`/bridge/stop`,{method:`POST`}),getChats:()=>M(`/chats/list`),classifyChats:({force:e=!1,limit:t}={})=>{let n=new URLSearchParams;return e&&n.set(`force`,`true`),t&&n.set(`limit`,String(t)),M(`/chats/classify`+(n.toString()?`?${n.toString()}`:``),{method:`POST`,body:JSON.stringify({force:e,limit:t})})},healthV2:()=>M(`/health`),validateKey:e=>M(`/setup/validate-key`,{method:`POST`,body:JSON.stringify({key:e})}),whitelistGroups:e=>M(`/groups/whitelist`,{method:`POST`,body:JSON.stringify({jids:e})}),getGroupsV2:()=>M(`/groups`),getDashboard:e=>M(`/dashboard${e?`?group_jid=${encodeURIComponent(e)}`:``}`),getTask:e=>M(`/tasks/${e}`),getTaskMessages:e=>M(`/tasks/${e}/messages`),updateTask:(e,t)=>M(`/tasks/${e}`,{method:`PATCH`,body:JSON.stringify(t)}),discoverTasks:e=>M(`/pipeline/discover`,{method:`POST`,body:JSON.stringify({group_jids:e})}),refreshTasks:e=>M(`/pipeline/refresh`,{method:`POST`,body:JSON.stringify({group_jids:e})}),deepDive:e=>M(`/pipeline/deep-dive`,{method:`POST`,body:JSON.stringify({task_id:e})}),discoverTasksStream:async({jids:e,onMeta:t,onGroup:n,onDone:r,onError:i}={})=>{let a;try{a=await fetch(`/api/pipeline/discover/stream`,{method:`POST`,headers:{"Content-Type":`application/json`},body:JSON.stringify({group_jids:e})})}catch(e){return i&&i({error:String(e)}),{ok:!1,error:String(e)}}return oe(a,{meta:t,group:n,done:r,error:i})},refreshTasksStream:async({jids:e,onMeta:t,onTask:n,onNewTask:r,onDone:i,onError:a}={})=>{let o;try{o=await fetch(`/api/pipeline/refresh/stream`,{method:`POST`,headers:{"Content-Type":`application/json`},body:JSON.stringify({group_jids:e})})}catch(e){return a&&a({error:String(e)}),{ok:!1,error:String(e)}}return oe(o,{meta:t,task:n,new_task:r,done:i,error:a})},classifyChatsStream:async({force:e=!1,limit:t,onMeta:n,onChat:r,onDone:i,onError:a}={})=>{let o;try{o=await fetch(`/api/chats/classify/stream`,{method:`POST`,headers:{"Content-Type":`application/json`},body:JSON.stringify({force:e,limit:t})})}catch(e){return a&&a({error:String(e)}),{ok:!1,error:String(e)}}if(!o.ok)return a&&a({error:`HTTP ${o.status}`}),{ok:!1,error:`HTTP ${o.status}`};if(!o.body||!o.body.getReader)return a&&a({error:`Streaming not supported in this browser.`}),{ok:!1,error:`Streaming not supported`};let s=o.body.getReader(),c=new TextDecoder,l=``;try{for(;;){let{value:e,done:t}=await s.read();if(t)break;l+=c.decode(e,{stream:!0});let o;for(;(o=l.indexOf(`

`))>=0;){let e=l.slice(0,o);l=l.slice(o+2);let t=`message`,s=``;for(let n of e.split(`
`))n.startsWith(`event:`)?t=n.slice(6).trim():n.startsWith(`data:`)&&(s+=n.slice(5).trim());if(!s)continue;let c;try{c=JSON.parse(s)}catch{c=null}c&&(t===`meta`&&n?n(c):t===`chat`&&r?r(c):t===`done`&&i?i(c):t===`error`&&a&&a(c))}}}catch(e){return a&&a({error:String(e)}),{ok:!1,error:String(e)}}return{ok:!0}},updateChatCategory:(e,t)=>M(`/chats/classify/update_category`,{method:`POST`,body:JSON.stringify({jid:e,category:t})}),extractTasks:e=>M(`/tasks/extract`,{method:`POST`,body:JSON.stringify({chats:e})}),extractTasksStream:async({chats:e,onMeta:t,onChat:n,onDone:r,onError:i}={})=>{let a;try{a=await fetch(`/api/tasks/extract/stream`,{method:`POST`,headers:{"Content-Type":`application/json`},body:JSON.stringify({chats:e})})}catch(e){return i&&i({error:String(e)}),{ok:!1,error:String(e)}}if(!a.ok)return i&&i({error:`HTTP ${a.status}`}),{ok:!1,error:`HTTP ${a.status}`};if(!a.body||!a.body.getReader)return i&&i({error:`Streaming not supported in this browser.`}),{ok:!1,error:`Streaming not supported`};let o=a.body.getReader(),s=new TextDecoder,c=``;try{for(;;){let{value:e,done:a}=await o.read();if(a)break;c+=s.decode(e,{stream:!0});let l;for(;(l=c.indexOf(`

`))>=0;){let e=c.slice(0,l);c=c.slice(l+2);let a=`message`,o=``;for(let t of e.split(`
`))t.startsWith(`event:`)?a=t.slice(6).trim():t.startsWith(`data:`)&&(o+=t.slice(5).trim());if(!o)continue;let s;try{s=JSON.parse(o)}catch{s=null}s&&(a===`meta`&&t?t(s):a===`chat`&&n?n(s):a===`done`&&r?r(s):a===`error`&&i&&i(s))}}}catch(e){return i&&i({error:String(e)}),{ok:!1,error:String(e)}}return{ok:!0}},getTasks:e=>M(`/tasks${e?`?group_jid=${encodeURIComponent(e)}`:``}`),updateTaskStatus:(e,t)=>M(`/tasks/update_status`,{method:`POST`,body:JSON.stringify({task_id:e,status:t})}),sendNudge:(e,t)=>M(`/send`,{method:`POST`,body:JSON.stringify({task_id:e,message:t})}),getGroups:()=>M(`/groups`),getHistory:()=>M(`/history`),generateNudges:e=>M(`/nudge/generate`,{method:`POST`,body:JSON.stringify({task_id:e})}),getPersona:()=>M(`/persona`),savePersona:e=>M(`/persona`,{method:`POST`,body:JSON.stringify({persona:e})}),generatePersona:()=>M(`/persona/generate`,{method:`POST`})};async function oe(e,t={}){if(!e.ok)return t.error&&t.error({error:`HTTP ${e.status}`}),{ok:!1,error:`HTTP ${e.status}`};if(!e.body||!e.body.getReader)return t.error&&t.error({error:`Streaming not supported in this browser.`}),{ok:!1,error:`Streaming not supported`};let n=e.body.getReader(),r=new TextDecoder,i=``;try{for(;;){let{value:e,done:a}=await n.read();if(a)break;i+=r.decode(e,{stream:!0});let o;for(;(o=i.indexOf(`

`))>=0;){let e=i.slice(0,o);i=i.slice(o+2);let n=`message`,r=``;for(let t of e.split(`
`))t.startsWith(`event:`)?n=t.slice(6).trim():t.startsWith(`data:`)&&(r+=t.slice(5).trim());if(!r)continue;let a;try{a=JSON.parse(r)}catch{a=null}if(!a)continue;let s=t[n];s&&s(a)}}}catch(e){return t.error&&t.error({error:String(e)}),{ok:!1,error:String(e)}}return{ok:!0}}function se(e,t){let n=document.createElement(`section`);n.className=`phase phase-pairing fade-in`,n.innerHTML=`
    <div class="pairing-card">
      <div class="pairing-brand">
        <div class="pairing-brand-mark">
          <img src="/mosaic-logo-mark.svg" alt="Mosaic" width="40" height="40" />
        </div>
        <div class="pairing-brand-text">
          <h2>Mosaic</h2>
          <p>Your life, pieced together.</p>
        </div>
      </div>

      <div class="pairing-status">
        <div class="pairing-status-dot" data-status-dot></div>
        <div class="pairing-status-text">
          <strong data-status-headline>Checking bridge…</strong>
          <span data-status-sub>Looking for a running wa-bridge process.</span>
        </div>
      </div>

      <div class="pairing-qr-wrap" data-qr-wrap style="display:none;">
        <p class="pairing-qr-hint">
          Scan from <em>WhatsApp → Settings → Linked Devices</em>
        </p>
        <div class="pairing-qr-canvas" data-qr-canvas></div>
      </div>

      <div class="pairing-qr-pending" data-qr-pending style="display:none;">
        <div class="pairing-spinner"></div>
        <p class="pairing-qr-hint">Waiting for QR code from WhatsApp servers…</p>
      </div>

      <div class="pairing-logout">
        <button class="btn-outline" data-logout-btn>Log out &amp; start over</button>
      </div>

      <div class="pairing-debug" data-debug-log></div>
    </div>
  `,e.appendChild(n);let r=n.querySelector(`[data-status-dot]`),i=n.querySelector(`[data-status-headline]`),a=n.querySelector(`[data-status-sub]`),o=n.querySelector(`[data-qr-wrap]`),s=n.querySelector(`[data-qr-canvas]`),c=n.querySelector(`[data-qr-pending]`),l=n.querySelector(`[data-logout-btn]`),u=n.querySelector(`[data-debug-log]`);function d(e){let t=new Date().toLocaleTimeString(),n=document.createElement(`div`);for(n.className=`pairing-debug-line`,n.textContent=`[${t}] ${e}`,u.appendChild(n),console.log(`[Pairing] ${e}`);u.children.length>15;)u.removeChild(u.firstChild)}let f=``,p=!1;async function m(){if(!p){p=!0,d(`startBridge() called`);try{let e=await N.bridgeStart();d(`bridgeStart response: ${JSON.stringify(e)}`),!e.ok&&e.error&&(i.textContent=`Cannot start bridge`,a.textContent=e.error,r.classList.add(`is-offline`))}catch(e){d(`bridgeStart error: ${e}`)}}}function h(e,t){r.classList.remove(`is-offline`,`is-pairing`,`is-connected`),e===`offline`?(r.classList.add(`is-offline`),i.textContent=`Bridge is offline`,a.textContent=`Waiting for the WhatsApp bridge to start…`,o.style.display=`none`,c.style.display=`none`):e===`pairing`?(r.classList.add(`is-pairing`),t?(i.textContent=`Waiting for QR scan…`,a.textContent=`Bridge is running. Scan the QR code below with your phone.`,c.style.display=`none`):(i.textContent=`Starting bridge…`,a.textContent=`Waiting for QR code from WhatsApp servers…`,o.style.display=`none`,c.style.display=`block`)):e===`connected`&&(r.classList.add(`is-connected`),i.textContent=`Connected`,a.textContent=`WhatsApp is ready. Continuing…`,o.style.display=`none`,c.style.display=`none`)}async function g(e){if(!(!e||e===f)){f=e;try{s.innerHTML=await ie.toString(e,{type:`svg`,width:320,margin:4,color:{dark:`#000000`,light:`#ffffff`}});let t=s.querySelector(`svg`);t&&(t.setAttribute(`width`,`320`),t.setAttribute(`height`,`320`),t.style.display=`block`,t.style.shapeRendering=`crispEdges`)}catch{s.innerHTML=``}}}let _=!1,v=0,y=0;async function b(){for(d(`poll() started, calling startBridge()`),m();!_;){v++;try{let[e,t]=await Promise.all([N.bridgeStatus(),N.bridgeQR().catch(e=>(d(`bridgeQR error: ${e}`),{qr_raw:``,event:`error`}))]),n=e.status||`offline`,r=!!(t.qr_raw&&t.event===`code`);if(d(`poll #${v} | status=${n} | qrEvent=${t.event} | qrReady=${r} | qrRawLen=${(t.qr_raw||``).length}`),h(n,r),n===`connected`){await new Promise(e=>setTimeout(e,900)),Q(X.WHITELIST);return}n===`offline`?(y++,y>=2&&(d(`offline for ${y} polls, restarting bridge`),p=!1,m(),y=0)):y=0,r&&(o.style.display=`block`,await g(t.qr_raw))}catch(e){d(`poll #${v} caught error: ${e}`),h(`offline`)}await new Promise(e=>setTimeout(e,2e3))}d(`poll loop stopped`)}l.addEventListener(`click`,async()=>{if(confirm(`This will erase all data and disconnect WhatsApp.

You will need to enter your Gemini key again and scan a new QR code.

Continue?`)){try{await N.reset()}catch{}window.location.reload()}}),h(`offline`),b();let x=new MutationObserver(()=>{document.contains(n)||(_=!0,x.disconnect())});x.observe(document.getElementById(`app`),{childList:!0})}var P=[`work`,`personal`],F={work:`Work`,personal:`Personal`},I={work:`work`,personal:`home`},L=e=>String(e||``).toLowerCase()===`work`?`work`:`personal`,R=e=>F[L(e)],ce=e=>String(e||``).split(/\s+/).filter(Boolean).slice(0,2).map(e=>e[0]).join(``).toUpperCase()||`?`,z=`application/x-taskdog-jid`;function le(e,t){let n=document.createElement(`section`);n.className=`phase phase-classifier fade-in`,n.innerHTML=`
    <div class="cls-page-head">
      <div>
        <h2>Intelligence Engine</h2>
        <p data-subtitle>Categorizing your top 100 active WhatsApp threads…</p>
      </div>
      <div class="cls-model-pill">
        <span class="material-symbols-outlined">psychology</span>
        Model: Mosaic-v2.1
      </div>
    </div>

    <div class="cls-toolbar">
      <button class="cls-toolbar-btn" data-recat>
        <span class="material-symbols-outlined">refresh</span>
        Re-categorize all
      </button>
      <div class="cls-meter"><div class="cls-meter-fill" data-meter></div></div>
      <div class="cls-meter-text">
        <span data-classified>0</span> / <span data-total>0</span> classified
      </div>
    </div>

    <div class="cls-engine cls-engine-direct" data-playfield>
      <div class="cls-tray cls-tray-direct" data-tray="work">
        <div class="cls-tray-head">
          <span class="cls-tray-ico cls-tray-ico-work">
            <span class="material-symbols-outlined fill">${I.work}</span>
          </span>
          <span class="cls-tray-name">${F.work}</span>
          <span class="cls-tray-count" data-count="work">0 items</span>
        </div>
        <div class="cls-tray-body cls-tray-body-direct" data-tray-body="work" data-dropzone="work">
          <div class="cls-tray-empty" data-empty="work">No work groups yet.</div>
        </div>
      </div>

      <div class="cls-tray cls-tray-direct" data-tray="personal">
        <div class="cls-tray-head">
          <span class="cls-tray-ico cls-tray-ico-personal">
            <span class="material-symbols-outlined fill">${I.personal}</span>
          </span>
          <span class="cls-tray-name">${F.personal}</span>
          <span class="cls-tray-count" data-count="personal">0 items</span>
        </div>
        <div class="cls-tray-body cls-tray-body-direct" data-tray-body="personal" data-dropzone="personal">
          <div class="cls-tray-empty" data-empty="personal">No personal groups yet.</div>
        </div>
      </div>
    </div>

    <p class="cls-hint">
      <span class="material-symbols-outlined">drag_indicator</span>
      Drag a card to move it between Work and Personal.
    </p>

    <div class="cls-actionbar is-show" data-actionbar>
      <div class="cls-actionbar-inner">
        <div class="cls-ab-count" data-selected-count>0</div>
        <div class="cls-ab-text">
          <strong>Groups Whitelisted</strong>
          <span data-selected-breakdown>Select at least 1 group to proceed</span>
        </div>
        <button class="btn btn-primary" data-proceed>
          Extract tasks
          <span class="material-symbols-outlined" style="font-size:18px">arrow_forward</span>
        </button>
      </div>
    </div>

    <div class="cls-overlay" data-overlay>
      <div class="cls-success">
        <div class="cls-success-mark">
          <span class="material-symbols-outlined">check_circle</span>
        </div>
        <h3>All set.</h3>
        <p>Mosaic will dig through <b data-success-n>0</b> groups and fetch your action items.</p>
        <div class="cls-success-chips" data-success-chips></div>
        <div class="cls-success-actions">
          <button class="btn" data-success-back>Back to sorting</button>
          <button class="btn btn-primary" data-success-go>
            Start extraction
            <span class="material-symbols-outlined" style="font-size:18px">arrow_forward</span>
          </button>
        </div>
      </div>
    </div>
  `,e.appendChild(n);let r=e=>n.querySelector(e),i={subtitle:r(`[data-subtitle]`),classified:r(`[data-classified]`),total:r(`[data-total]`),meter:r(`[data-meter]`),actionbar:r(`[data-actionbar]`),abCount:r(`[data-selected-count]`),abText:r(`[data-selected-breakdown]`),overlay:r(`[data-overlay]`),successN:r(`[data-success-n]`),successChips:r(`[data-success-chips]`)},a=new Map,o=0,s=0,c=!1;function l(e){let t=document.createElement(`div`);return t.className=`cls-block cls-block-direct`,t.dataset.id=e.jid,t.dataset.cat=e.category,t.draggable=!0,e.selected&&t.classList.add(`is-selected`),t.title=e.tldr||e.name,t.innerHTML=`
      <div class="cls-avatar">${B(ce(e.name))}</div>
      <div class="cls-block-main">
        <div class="cls-block-name">${B(e.name)}</div>
        <div class="cls-block-tldr">${B(e.tldr||`No summary available.`)}</div>
      </div>
      <button class="cls-tick-btn" data-tick aria-label="${e.selected?`Unselect`:`Select`} group" type="button">
        <span class="material-symbols-outlined">check</span>
      </button>
    `,t.querySelector(`[data-tick]`).addEventListener(`click`,n=>{n.stopPropagation(),e.selected=!e.selected,t.classList.toggle(`is-selected`,e.selected),t.querySelector(`[data-tick]`).setAttribute(`aria-label`,`${e.selected?`Unselect`:`Select`} group`),f()}),t.addEventListener(`dragstart`,n=>{n.dataTransfer.effectAllowed=`move`,n.dataTransfer.setData(z,e.jid),n.dataTransfer.setData(`text/plain`,e.jid),t.classList.add(`is-dragging`)}),t.addEventListener(`dragend`,()=>{t.classList.remove(`is-dragging`),n.querySelectorAll(`.cls-tray-body-direct.is-drop-target`).forEach(e=>e.classList.remove(`is-drop-target`))}),t}function u(e){let t=e.jid;if(a.has(t))return;let r=L(e.category),i={jid:t,name:e.name||t,category:r,tldr:e.tldr||``,selected:!!e.is_whitelisted,fromCache:!!e.from_cache,el:null};i.el=l(i),a.set(t,i);let o=n.querySelector(`[data-tray-body="${r}"]`);if(o.appendChild(i.el),o.querySelectorAll(`.cls-block-direct`).length>0){let e=o.querySelector(`.cls-tray-empty`);e&&(e.style.display=`none`)}s++}function d(){let e={work:0,personal:0};a.forEach(t=>{e[t.category]=(e[t.category]||0)+1}),P.forEach(t=>{let r=n.querySelector(`[data-count="${t}"]`),i=e[t];r.textContent=`${i} ${i===1?`item`:`items`}`;let a=n.querySelector(`[data-tray-body="${t}"]`).querySelector(`.cls-tray-empty`);a.style.display=i===0?``:`none`}),i.classified.textContent=String(s),i.total.textContent=String(o),i.meter.style.transform=`scaleX(${o?s/o:0})`}function f(){let e=[...a.values()].filter(e=>e.selected);if(i.abCount.textContent=String(e.length),i.abCount.classList.toggle(`is-active`,e.length>0),e.length<1)i.abText.innerHTML=`Select at least 1 group to proceed`;else{let t={work:0,personal:0};e.forEach(e=>{t[e.category]=(t[e.category]||0)+1});let n=[];t.work&&n.push(`<b>${t.work}</b> ${F.work}`),t.personal&&n.push(`<b>${t.personal}</b> ${F.personal}`),i.abText.innerHTML=n.join(` · `)||`<b>${e.length}</b> groups selected`}}function p(){P.forEach(e=>{let t=n.querySelector(`[data-dropzone="${e}"]`);t&&(t.addEventListener(`dragover`,e=>{[...e.dataTransfer.types].some(e=>e===z||e===`text/plain`)&&(e.preventDefault(),e.dataTransfer.dropEffect=`move`,t.classList.add(`is-drop-target`))}),t.addEventListener(`dragleave`,e=>{e.relatedTarget&&t.contains(e.relatedTarget)||t.classList.remove(`is-drop-target`)}),t.addEventListener(`drop`,async n=>{n.preventDefault(),t.classList.remove(`is-drop-target`);let r=n.dataTransfer.getData(z)||n.dataTransfer.getData(`text/plain`);r&&await m(r,e)}))})}async function m(e,t){let r=a.get(e);if(!r)return;let i=R(t);if(r.category===t)return;let o=n.querySelector(`[data-tray-body="${r.category}"]`),s=n.querySelector(`[data-tray-body="${t}"]`);if(!(!o||!s)){o.removeChild(r.el),s.appendChild(r.el),r.category=t,r.el.dataset.cat=t,d(),f();try{let t=await N.updateChatCategory(e,i);t.ok||console.warn(`updateChatCategory failed`,t)}catch(e){console.warn(`updateChatCategory error`,e)}}}async function h(e=!1){c||(c=!0,a.forEach(e=>{e.el&&e.el.parentNode&&e.el.parentNode.removeChild(e.el)}),a.clear(),s=0,o=0,i.subtitle.textContent=e?`Re-classifying all groups…`:`Loading…`,d(),f(),await N.classifyChatsStream({force:e,onMeta:e=>{o=e.total||0,i.total.textContent=String(o)},onChat:e=>{u(e),d(),f()},onError:e=>{i.subtitle.textContent=`Error: ${e.error||`Unknown error`}`,c=!1},onDone:()=>{let e=0,t=0;a.forEach(n=>{n.fromCache?e++:t++}),i.subtitle.textContent=t===0?`All ${e} groups loaded from cache`:`${e} cached · ${t} freshly classified`,i.meter.style.transform=`scaleX(1)`,c=!1}}))}r(`[data-recat]`).addEventListener(`click`,()=>{c||h(!0)}),r(`[data-proceed]`).addEventListener(`click`,()=>{let e=[...a.values()].filter(e=>e.selected);e.length<1||(i.successN.textContent=String(e.length),i.successChips.innerHTML=e.slice(0,6).map(e=>`<span class="cls-success-chip" data-cat="${e.category}"><span class="dot"></span>${B(e.name)}</span>`).join(``)+(e.length>6?`<span class="cls-success-chip">+${e.length-6} more</span>`:``),i.overlay.classList.add(`is-show`))}),r(`[data-success-back]`).addEventListener(`click`,()=>i.overlay.classList.remove(`is-show`)),i.overlay.addEventListener(`click`,e=>{e.target===i.overlay&&i.overlay.classList.remove(`is-show`)}),r(`[data-success-go]`).addEventListener(`click`,()=>{let e=[...a.values()].filter(e=>e.selected).map(e=>({jid:e.jid,name:e.name,category:R(e.category),tldr:e.tldr}));Q(X.EXTRACT,{selectedChats:e})}),p(),h(!1)}function B(e){return String(e||``).replace(/&/g,`&amp;`).replace(/</g,`&lt;`).replace(/>/g,`&gt;`).replace(/"/g,`&quot;`).replace(/'/g,`&#39;`)}var V=[`Reading 30 days of conversations…`,`Clustering messages into themes…`,`Identifying action items…`,`Drafting concise follow-ups…`,`Drafting moderate follow-ups…`,`Adding context-rich variants…`,`Finalising task cards…`];function ue(e,t){let n=t.selectedChats||[],r=document.createElement(`section`);r.className=`phase phase-extract fade-in`,r.innerHTML=`
    <div class="extract-stage">
      <div class="extract-rings">
        <div class="extract-ring-outer"></div>
        <div class="extract-ring-mid"></div>
        <div class="extract-ring-inner">
          <span class="material-symbols-outlined">data_usage</span>
        </div>
      </div>

      <h1 class="extract-headline">Analyzing 30 days of conversation…</h1>
      <div class="extract-mono" data-mono>Running Gemini Map-Reduce pipeline</div>
      <div class="extract-msg" data-msg>${V[0]}</div>

      <div class="extract-queue">
        <div class="extract-queue-head">
          <span class="label">Group Processing Queue</span>
          <span class="progress" data-progress>0 / ${n.length} Complete</span>
        </div>
        <div data-queue>
          ${n.map((e,t)=>`
            <div class="extract-queue-item ${t===0?`is-active`:`is-pending`}" data-queue-idx="${t}" data-jid="${fe(e.jid)}">
              <span class="material-symbols-outlined">${t===0?`sync`:`schedule`}</span>
              <span class="extract-queue-item-name">${de(e.name)}</span>
              <span class="extract-queue-item-status">${t===0?`Processing`:`Pending`}</span>
            </div>
          `).join(``)}
        </div>
      </div>
    </div>
  `,e.appendChild(r);let i=r.querySelector(`[data-msg]`),a=r.querySelector(`[data-mono]`),o=r.querySelector(`[data-progress]`),s=Array.from(r.querySelectorAll(`.extract-queue-item`)),c=new Map(s.map(e=>[e.dataset.jid,e])),l={ok:0,no_messages:0,gemini_failed:0,save_failed:0,total:n.length},u=Date.now(),d=-1,f=setInterval(()=>{let e=Date.now()-u,t=Math.min(1,e/17e3),n=Math.min(V.length-1,Math.floor(t*V.length));n!==d&&(i.textContent=V[n],d=n)},200),p=setInterval(()=>{let e=l.ok+l.no_messages+l.gemini_failed+l.save_failed;s.forEach(e=>{e.classList.contains(`is-done`)||e.classList.contains(`is-warn`)||e.classList.contains(`is-fail`)}),o.textContent=`${e} / ${l.total} Complete`},300);function m(e){let t=c.get(e.jid);if(!t)return;let n=t.querySelector(`.extract-queue-item-status`),r=t.querySelector(`.material-symbols-outlined`),i=e.status;if(t.classList.remove(`is-active`,`is-pending`),i===`ok`){l.ok+=1,t.classList.add(`is-done`),r.textContent=`check_circle`;let i=e.task_count||0,a=e.theme_count||0;n.textContent=i?`Done · ${i} task${i===1?``:`s`}${a?` · ${a} theme${a===1?``:`s`}`:``}`:`Done`}else i===`no_messages`?(l.no_messages+=1,t.classList.add(`is-warn`),r.textContent=`chat_off`,n.textContent=`No 30-day history`):i===`save_failed`?(l.save_failed+=1,t.classList.add(`is-fail`),r.textContent=`error`,n.textContent=`Save failed`):(l.gemini_failed+=1,t.classList.add(`is-fail`),r.textContent=`error`,n.textContent=`Gemini failed`);h(),o.textContent=`${l.ok+l.no_messages+l.gemini_failed+l.save_failed} / ${l.total} Complete`}function h(){if(l.ok+l.no_messages+l.gemini_failed+l.save_failed!==0)if(l.gemini_failed===0&&l.save_failed===0&&l.no_messages===0)a.textContent=`${l.ok} group${l.ok===1?``:`s`} processed`;else{let e=[`${l.ok} ok`];l.no_messages&&e.push(`${l.no_messages} no history`),l.gemini_failed&&e.push(`${l.gemini_failed} failed`),l.save_failed&&e.push(`${l.save_failed} save err`),a.textContent=e.join(` · `)}}(async()=>{let e=!0,t=await N.extractTasksStream({chats:n,onMeta:e=>{l.total=e.total||l.total},onChat:m,onError:async t=>{console.warn(`extract stream errored, falling back:`,t),e=!1;let r=await N.extractTasks(n);if(!r.ok){_(r.error||`Failed to extract tasks`);return}let i=new Map((r.details||[]).map(e=>[e.jid,e]));s.forEach(e=>{let t=e.dataset.jid,n=i.get(t);n&&m(n)}),g()},onDone:()=>g()});e&&!t.ok&&_(t.error||`Stream interrupted`)})();function g(){clearInterval(f),clearInterval(p),h();let e=l.ok+l.no_messages+l.gemini_failed+l.save_failed;e>=l.total&&(i.textContent=l.gemini_failed===0&&l.save_failed===0?`Done — opening Kanban…`:`Done with issues — opening Kanban…`,o.textContent=`${e} / ${l.total} Complete`),setTimeout(()=>Q(X.KANBAN),900)}function _(e){clearInterval(f),clearInterval(p),i.textContent=`Error: ${e}`,a.textContent=`Pipeline aborted`,s.forEach(e=>{if(e.classList.contains(`is-done`)||e.classList.contains(`is-warn`)||e.classList.contains(`is-fail`))return;let t=e.querySelector(`.extract-queue-item-status`),n=e.querySelector(`.material-symbols-outlined`);e.classList.remove(`is-active`,`is-pending`),n.textContent=`error`,t.textContent=`Failed`})}}function de(e){return String(e).replace(/&/g,`&amp;`).replace(/</g,`&lt;`).replace(/>/g,`&gt;`)}function fe(e){return String(e).replace(/&/g,`&amp;`).replace(/"/g,`&quot;`).replace(/</g,`&lt;`).replace(/>/g,`&gt;`)}var pe=[{key:`concise`,label:`Concise`,tagline:`Quick check-in`},{key:`moderate`,label:`Moderate`,tagline:`Polite follow-up`},{key:`with_context`,label:`Contextual`,tagline:`Detailed, references chat`}],me=[{key:`not started`,label:`Not Started`},{key:`pending`,label:`Pending`},{key:`done`,label:`Done`}];function H(e,t,n){let{onClose:r,onUpdateStatus:i,onSend:a}=n,o=t.suggested_responses||{},s=he(t.status);e.innerHTML=`
    <div class="drawer-head">
      <div class="drawer-eyebrow">
        <span class="badge ${s.cls}">
          <span class="dot"></span>${s.label}
        </span>
        <span class="material-symbols-outlined">forum</span>
        <span style="color:var(--on-surface-muted)">${U(t.group_name||`Group`)}</span>
      </div>
      <h2 class="drawer-title">${U(t.title)}</h2>
      <button class="drawer-close" data-close aria-label="Close">
        <span class="material-symbols-outlined">close</span>
      </button>
    </div>

    <div class="drawer-body">
      <section class="drawer-section">
        <div class="section-label"><span>Details</span></div>
        ${t.assignee?`
          <div class="drawer-kv">
            <span class="drawer-kv-label">Assignee</span>
            <span class="assignee-pill">@${U(t.assignee)}</span>
          </div>
        `:``}
        ${t.theme_name?`
          <div class="drawer-kv">
            <span class="drawer-kv-label">Theme</span>
            <span class="badge badge-work">${U(t.theme_name)}</span>
          </div>
        `:``}
        <div class="drawer-kv">
          <span class="drawer-kv-label">Source</span>
          <span class="drawer-kv-val">
            <span class="material-symbols-outlined" style="font-size:16px;color:var(--on-surface-muted)">groups</span>
            ${U(t.group_name||`—`)}
          </span>
        </div>
      </section>

      <div class="drawer-divider"></div>

      <section class="drawer-section">
        <div class="section-label"><span>Conversation Context</span></div>
        <div class="context-text">${U(t.context||`No context available.`)}</div>
      </section>

      <div class="drawer-divider"></div>

      <section class="drawer-section">
        <div class="section-label"><span>Move to</span></div>
        <div class="status-flow" data-status-flow>
          ${me.map(e=>`
              <button class="status-flow-btn ${e.key===t.status?`is-active`:``}" data-status="${e.key}">
                ${e.label}
              </button>
            `).join(``)}
        </div>
      </section>

      <div class="drawer-divider"></div>

      <section class="drawer-section" data-suggest-section>
        <div class="section-label">
          <span>Suggested Actions</span>
          <span class="section-hint">Sent as you to the group</span>
        </div>
        <div class="response-stack" data-response-stack>
          ${pe.map(e=>{let t=o[e.key]||``;return`
              <div class="response-card" data-variant="${e.key}">
                <div class="response-card-head">
                  <div class="response-card-titles">
                    <div class="response-card-label">${e.label}</div>
                    <div class="response-card-tagline">${e.tagline}</div>
                  </div>
                  <button class="btn btn-primary response-send-btn" data-send-variant="${e.key}" ${t?``:`disabled`}>
                    <span class="material-symbols-outlined" style="font-size:16px">send</span>
                    Send
                  </button>
                </div>
                <div class="response-text">${U(t)||`<span class="response-empty">No suggestion available.</span>`}</div>
              </div>
            `}).join(``)}
        </div>
      </section>
    </div>
  `,e.querySelector(`[data-close]`).addEventListener(`click`,r),e.querySelectorAll(`[data-status]`).forEach(r=>{r.addEventListener(`click`,async()=>{let a=r.dataset.status;a!==t.status&&(await i(a),H(e,{...t,status:a},n))})}),e.querySelectorAll(`[data-send-variant]`).forEach(t=>{t.addEventListener(`click`,async()=>{let n=o[t.dataset.sendVariant];if(!n)return;let i=e.querySelectorAll(`[data-send-variant]`);i.forEach(e=>{e.disabled=!0});let s=t.innerHTML;t.innerHTML=`<span class="spinner"></span> Sending…`,await a(n)?(t.innerHTML=`<span class="material-symbols-outlined" style="font-size:16px">check_circle</span> Sent!`,setTimeout(r,700)):(t.innerHTML=s,i.forEach(e=>{e.disabled=!1}))})})}function he(e){return e===`done`?{cls:`badge-done`,label:`Done`}:e===`pending`?{cls:`badge-pending`,label:`Pending`}:{cls:`badge-not-started`,label:`Not Started`}}function U(e){return String(e||``).replace(/&/g,`&amp;`).replace(/</g,`&lt;`).replace(/>/g,`&gt;`).replace(/"/g,`&quot;`).replace(/'/g,`&#39;`)}function ge(e,t,n){e.innerHTML=`
    <div class="drawer-head">
      <div class="drawer-eyebrow">
        <span class="material-symbols-outlined" style="color:var(--primary)">history</span>
        <span style="color:var(--on-surface-muted)">Nudge history</span>
      </div>
      <h2 class="drawer-title">Sent messages</h2>
      <button class="drawer-close" data-close aria-label="Close">
        <span class="material-symbols-outlined">close</span>
      </button>
    </div>
    <div class="drawer-body">
      ${t.length===0?`<div class="empty-state">
               <span class="material-symbols-outlined">forum</span>
               No messages sent yet.
             </div>`:t.map(e=>`
          <div class="history-item">
            <div class="history-meta">
              <span class="material-symbols-outlined">schedule</span>
              <span class="history-time">${_e(e.sent_at)}</span>
              <span style="color:var(--outline-variant)">·</span>
              <span class="history-group">${W(e.group_name||``)}</span>
            </div>
            <div class="history-task">${W(e.task_title||``)}</div>
            <div class="history-text">${W(e.sent_text||``)}</div>
          </div>
        `).join(``)}
    </div>
  `,e.querySelector(`[data-close]`).addEventListener(`click`,n)}function _e(e){if(!e)return``;try{let t=new Date(e);return isNaN(t.getTime())?e:t.toLocaleString()}catch{return e}}function W(e){return String(e||``).replace(/&/g,`&amp;`).replace(/</g,`&lt;`).replace(/>/g,`&gt;`).replace(/"/g,`&quot;`).replace(/'/g,`&#39;`)}var G=[{key:`not started`,label:`Not Started`,cls:`st-not-started`},{key:`pending`,label:`Pending`,cls:`st-pending`},{key:`done`,label:`Done`,cls:`st-done`}],ve={Work:`badge-work`,Personal:`badge-personal`,Others:`badge-others`};function ye(e,t){let n=document.createElement(`section`);n.className=`phase phase-kanban fade-in`,n.innerHTML=`
    <aside class="kanban-sidebar">
      <div>
        <div class="section-label">Category</div>
        <div class="chip-row" data-category-chips>
          <span class="chip" data-cat="all">All</span>
          <span class="chip" data-cat="Work">Work</span>
          <span class="chip" data-cat="Personal">Personal</span>
          <span class="chip" data-cat="Others">Others</span>
        </div>
      </div>
      <div>
        <div class="group-section-head">
          <div class="section-label">Groups</div>
          <div class="group-bulk">
            <button class="group-bulk-btn" data-bulk="all">All</button>
            <button class="group-bulk-btn" data-bulk="none">None</button>
            <button class="group-bulk-btn" data-bulk="invert">Invert</button>
          </div>
        </div>
        <div class="group-list" data-group-list>
          <div class="empty-mini">Loading…</div>
        </div>
      </div>
    </aside>

    <div class="kanban-main">
      <div class="kanban-head">
        <h2>Your Kanban</h2>
        <div class="kanban-meta" data-meta></div>
      </div>
      <div class="kanban-board" data-board>
        ${G.map(e=>`
            <div class="kanban-col" data-col="${e.key}">
              <div class="kanban-col-head">
                <span class="col-dot ${e.cls}"></span>
                <span class="col-label">${e.label}</span>
                <span class="col-count" data-count="${e.key}">0</span>
              </div>
              <div class="col-body" data-drop="${e.key}"></div>
            </div>
          `).join(``)}
      </div>
    </div>
  `,e.appendChild(n);let r=[],i=[],a=new Set,o=t.activeCategory&&t.activeCategory!==`all`?t.activeCategory.charAt(0).toUpperCase()+t.activeCategory.slice(1):`all`;function s(){n.querySelectorAll(`[data-cat]`).forEach(e=>{e.classList.toggle(`is-active`,e.dataset.cat===o)})}s();async function c(){let[e,t]=await Promise.all([N.getTasks(),N.getGroups()]);e.ok&&(r.length=0,r.push(...e.tasks)),t.ok&&(i.length=0,i.push(...t.groups)),a.size===0&&i.length>0&&i.forEach(e=>a.add(e.jid)),l(),u()}function l(){let e=n.querySelector(`[data-group-list]`);if(i.length===0){e.innerHTML=`<div class="empty-mini">No groups yet.</div>`;return}e.innerHTML=i.map(e=>`
        <label class="group-item" data-jid="${be(e.jid)}">
          <input type="checkbox" ${a.has(e.jid)?`checked`:``} />
          <span class="group-dot cat-${e.category}"></span>
          <span class="group-name">${K(e.name)}</span>
          <span class="group-tldr">${K(e.tldr||``)}</span>
        </label>
      `).join(``),e.querySelectorAll(`.group-item`).forEach(e=>{e.addEventListener(`click`,t=>{if(t.target.tagName!==`INPUT`){let t=e.querySelector(`input`);t.checked=!t.checked}let n=e.dataset.jid;e.querySelector(`input`).checked?a.add(n):a.delete(n),u()})})}function u(){let e=n.querySelector(`[data-board]`),t=n.querySelector(`[data-meta]`),s=a.size===0,c=a.size===i.length&&i.length>0,l=r.filter(e=>{if(s||!c&&!a.has(e.group_jid))return!1;if(o!==`all`){let t=i.find(t=>t.jid===e.group_jid);if(!t||t.category!==o)return!1}return!0});s?t.textContent=`No groups selected`:c?t.textContent=`${l.length} task${l.length===1?``:`s`} visible`:t.textContent=`${l.length} of ${r.length} tasks visible · ${a.size} of ${i.length} groups`;let u={"not started":[],pending:[],done:[]};l.forEach(e=>u[e.status]?.push(e)),G.forEach(t=>{try{let n=e.querySelector(`[data-col="${t.key}"]`);if(!n)return;let r=n.querySelector(`[data-drop="${t.key}"]`),i=n.querySelector(`[data-count="${t.key}"]`);r.innerHTML=``;let a=u[t.key]||[];if(i.textContent=a.length,a.length===0){let e=document.createElement(`div`);e.className=`col-empty`,s?e.innerHTML=`<span class="material-symbols-outlined">folder_off</span><p>Select a group on the left.</p>`:t.key===`done`?e.innerHTML=`<span class="material-symbols-outlined">check_circle</span><p>No completed tasks yet.</p>`:e.innerHTML=`<span class="material-symbols-outlined">inbox</span><p>Nothing here.</p>`,r.appendChild(e)}else a.forEach(e=>r.appendChild(d(e)))}catch(e){console.error(`[Kanban] failed to render column ${t.key}:`,e)}}),p()}function d(e){let t=document.createElement(`div`);t.className=`task-card`,t.dataset.taskId=e.id,t.draggable=!0;let n=G.find(t=>t.key===e.status)||G[0],r=i.find(t=>t.jid===e.group_jid)?.category||`Others`;return t.innerHTML=`
      <div class="card-accent ${n.cls}"></div>
      <div class="card-row-1">
        <span class="badge ${ve[r]||`badge-others`}">${K(r)}</span>
        ${e.assignee?`<span class="assignee">@${K(e.assignee)}</span>`:``}
      </div>
      <div class="card-title">${K(e.title)}</div>
      <div class="card-meta">
        <span class="card-theme">
          <span class="material-symbols-outlined" style="font-size:12px">${f(e.theme_name)}</span>
          ${K(e.theme_name||`Untitled`)}
        </span>
        <span class="card-group">
          <span class="dot cat-${r}"></span>
          ${K(e.group_name||``)}
        </span>
      </div>
    `,t.addEventListener(`click`,()=>m(e)),t}function f(e){let t=String(e||``).toLowerCase();return t.includes(`review`)?`rate_review`:t.includes(`deploy`)?`rocket_launch`:t.includes(`plan`)?`event`:t.includes(`contact`)?`contact_page`:t.includes(`design`)?`palette`:t.includes(`marketing`)?`campaign`:t.includes(`sales`)?`trending_up`:t.includes(`meeting`)?`groups`:`topic`}function p(){let e=n.querySelectorAll(`.task-card`),t=n.querySelectorAll(`[data-drop]`),i=null;e.forEach(e=>{e.addEventListener(`dragstart`,t=>{i=e.dataset.taskId,e.classList.add(`is-dragging`),t.dataTransfer.effectAllowed=`move`,t.dataTransfer.setData(`text/plain`,i)}),e.addEventListener(`dragend`,()=>{e.classList.remove(`is-dragging`),i=null})}),t.forEach(e=>{e.addEventListener(`dragover`,t=>{t.preventDefault(),e.classList.add(`is-drag-over`)}),e.addEventListener(`dragleave`,()=>e.classList.remove(`is-drag-over`)),e.addEventListener(`drop`,async t=>{t.preventDefault(),e.classList.remove(`is-drag-over`);let n=t.dataTransfer.getData(`text/plain`)||i,a=e.dataset.drop;if(!n)return;let o=r.find(e=>e.id===n);if(!o||o.status===a)return;let s=o.status;o.status=a,u();let c=await N.updateTaskStatus(n,a);c.ok||(o.status=s,u(),alert(`Failed to update: ${c.error}`))})})}function m(e){let t=document.createElement(`div`);t.className=`drawer-overlay`,document.body.appendChild(t);let n=document.createElement(`div`);n.className=`drawer`,document.body.appendChild(n);function i(){t.remove(),n.remove()}t.addEventListener(`click`,i),window.addEventListener(`keydown`,function e(t){t.key===`Escape`&&(i(),window.removeEventListener(`keydown`,e))}),H(n,e,{onClose:i,onUpdateStatus:async t=>{let n=e.status;e.status=t;let i=r.find(t=>t.id===e.id);i&&(i.status=t),u();let a=await N.updateTaskStatus(e.id,t);a.ok||(e.status=n,i&&(i.status=n),u(),alert(`Failed to update: ${a.error}`))},onSend:async t=>{let n=await N.sendNudge(e.id,t,e.group_jid);if(!n.ok)return alert(`Send failed: ${n.error}`),!1;e.status=`pending`;let i=r.find(t=>t.id===e.id);return i&&(i.status=`pending`),u(),!0}})}window.addEventListener(`taskdog:showHistory`,async()=>{let e=document.createElement(`div`);e.className=`drawer-overlay`,document.body.appendChild(e);let t=document.createElement(`div`);t.className=`drawer drawer-wide`,document.body.appendChild(t);function n(){e.remove(),t.remove()}e.addEventListener(`click`,n);let r=await N.getHistory();ge(t,r.ok?r.history:[],n)}),n.querySelectorAll(`[data-bulk]`).forEach(e=>{e.addEventListener(`click`,()=>{let t=e.dataset.bulk;t===`all`?i.forEach(e=>a.add(e.jid)):t===`none`?a.clear():t===`invert`&&i.forEach(e=>{a.has(e.jid)?a.delete(e.jid):a.add(e.jid)}),l(),u()})}),n.querySelectorAll(`[data-cat]`).forEach(e=>{e.addEventListener(`click`,()=>{o=e.dataset.cat;let t=Ie();t.activeCategory=o===`all`?`all`:o.toLowerCase(),s(),u()})}),window.addEventListener(`taskdog:setCategory`,e=>{let t=e.detail;o=t===`all`?`all`:t.charAt(0).toUpperCase()+t.slice(1),s(),u()}),c()}function K(e){return String(e||``).replace(/&/g,`&amp;`).replace(/</g,`&lt;`).replace(/>/g,`&gt;`).replace(/"/g,`&quot;`).replace(/'/g,`&#39;`)}function be(e){return String(e||``).replace(/"/g,`&quot;`)}function xe(e,t){let n=[{phase:X.DASHBOARD,label:`Dashboard`},{phase:X.WHITELIST,label:`Groups`}],r=document.createElement(`header`);r.className=`topbar`;let i=document.createElement(`div`);i.className=`topbar-brand`,i.innerHTML=`
    <div class="topbar-brand-mark">
      <img src="/mosaic-logo-mark.svg" alt="Mosaic" width="24" height="24" />
    </div>
    <div class="topbar-brand-text">
      <h1>Mosaic</h1>
      <p class="topbar-subtext">Your life, pieced together.</p>
      <div class="topbar-sync">
        <span class="topbar-sync-dot" data-sync-dot></span>
        <span data-sync-label>${Se(t.lastSynced)}</span>
      </div>
    </div>
  `,r.appendChild(i);let a=document.createElement(`nav`);a.className=`topbar-tabs`,n.forEach(e=>{let n=document.createElement(`button`);n.className=`topbar-tab`+(t.phase===e.phase?` is-active`:``),n.textContent=e.label,n.addEventListener(`click`,()=>Q(e.phase)),a.appendChild(n)}),r.appendChild(a);let o=document.createElement(`div`);o.className=`topbar-right`;let s=document.createElement(`button`);s.className=`topbar-icon`,s.title=`API Key Settings`,s.innerHTML=`<span class="material-symbols-outlined">key</span>`,s.addEventListener(`click`,()=>Q(X.APIKEY)),o.appendChild(s);let c=document.createElement(`button`);c.className=`topbar-icon topbar-logout`,c.title=`Logout`,c.innerHTML=`
    <span class="material-symbols-outlined">logout</span>
    <span class="topbar-logout-label">Logout</span>
  `,c.addEventListener(`click`,()=>Q(X.PAIRING)),o.appendChild(c);let l=document.createElement(`button`);l.className=`theme-toggle`;let u=localStorage.getItem(`taskdog-theme`)||`dark`;document.documentElement.setAttribute(`data-theme`,u),l.innerHTML=`<span class="material-symbols-outlined">${u===`light`?`dark_mode`:`light_mode`}</span>`,l.title=u===`light`?`Switch to dark mode`:`Switch to light mode`,l.addEventListener(`click`,()=>{let e=document.documentElement.getAttribute(`data-theme`)===`light`?`dark`:`light`;document.documentElement.setAttribute(`data-theme`,e),localStorage.setItem(`taskdog-theme`,e),l.querySelector(`.material-symbols-outlined`).textContent=e===`light`?`dark_mode`:`light_mode`,l.title=e===`light`?`Switch to dark mode`:`Switch to light mode`}),o.appendChild(l),r.appendChild(o),e.appendChild(r)}function Se(e){if(!e)return`Last Synced: just now`;try{let t=new Date(e);if(isNaN(t.getTime()))return`Last Synced: just now`;let n=Date.now()-t.getTime(),r=Math.floor(n/6e4);if(r<1)return`Last Synced: just now`;if(r<60)return`Last Synced: ${r} min ago`;let i=Math.floor(r/60);return i<24?`Last Synced: ${i} hr ago`:`Last Synced: ${t.toLocaleDateString()}`}catch{return`Last Synced: just now`}}function Ce(e,t){let n=document.createElement(`section`);n.className=`phase phase-apikey fade-in`,n.innerHTML=`
    <div class="apikey-card">
      <div class="apikey-brand">
        <div class="apikey-brand-mark">
          <img src="/mosaic-logo-mark.svg" alt="Mosaic" width="40" height="40" />
        </div>
        <div class="apikey-brand-text">
          <h2>Mosaic</h2>
          <p>Your life, pieced together.</p>
        </div>
      </div>

      <div class="apikey-body">
        <div class="apikey-step-label">Step 1 of 3 · API Key</div>
        <h3>Enter your Gemini API key</h3>
        <p class="apikey-desc">
          Mosaic uses Google Gemini to analyze your WhatsApp chats and extract tasks.
          Your key is stored securely in macOS Keychain and never sent to any server except Google.
        </p>

        <div class="apikey-input-row">
          <input
            type="password"
            class="apikey-input"
            placeholder="AIzaSy..."
            data-key-input
            autocomplete="off"
            spellcheck="false"
          />
          <button class="btn btn-primary" data-validate disabled>
            <span class="material-symbols-outlined" style="font-size:18px">key</span>
            Validate
          </button>
        </div>

        <div class="apikey-status" data-status></div>

        <div class="apikey-hint">
          <span class="material-symbols-outlined" style="font-size:16px">open_in_new</span>
          <a href="https://aistudio.google.com/app/apikey" target="_blank" rel="noopener">
            Get a free API key from Google AI Studio
          </a>
        </div>

        <div class="apikey-steps">
          <div class="apikey-step is-active">
            <div class="apikey-step-num">1</div>
            <span>API Key</span>
          </div>
          <div class="apikey-step">
            <div class="apikey-step-num">2</div>
            <span>WhatsApp Bridge</span>
          </div>
          <div class="apikey-step">
            <div class="apikey-step-num">3</div>
            <span>Select Groups</span>
          </div>
        </div>
      </div>
    </div>
  `,e.appendChild(n);let r=n.querySelector(`[data-key-input]`),i=n.querySelector(`[data-validate]`),a=n.querySelector(`[data-status]`);r.addEventListener(`input`,()=>{i.disabled=r.value.trim().length<10}),r.addEventListener(`keydown`,e=>{e.key===`Enter`&&!i.disabled&&i.click()}),i.addEventListener(`click`,async()=>{let e=r.value.trim();if(!e)return;i.disabled=!0,i.innerHTML=`<span class="spinner"></span> Validating…`,a.innerHTML=``;let t=await N.validateKey(e);t.ok?(i.innerHTML=`<span class="material-symbols-outlined" style="font-size:18px">check_circle</span> Valid!`,a.innerHTML=`
        <div class="apikey-success">
          <span class="material-symbols-outlined">check_circle</span>
          Key validated successfully. Continuing to WhatsApp bridge…
        </div>
      `,setTimeout(()=>Q(X.PAIRING),1200)):(i.disabled=!1,i.innerHTML=`<span class="material-symbols-outlined" style="font-size:18px">key</span> Validate`,a.innerHTML=`
        <div class="apikey-error">
          <span class="material-symbols-outlined">error</span>
          ${we(t.error||`Validation failed`)}
        </div>
      `)}),t.health&&t.health.gemini_key_set&&(r.value=``,r.placeholder=`Key set (${t.health.gemini_key_preview||`•••`})`,i.disabled=!1,i.innerHTML=`<span class="material-symbols-outlined" style="font-size:18px">arrow_forward</span> Continue`,i.addEventListener(`click`,()=>Q(X.PAIRING),{once:!0}))}function we(e){return String(e||``).replace(/&/g,`&amp;`).replace(/</g,`&lt;`).replace(/>/g,`&gt;`).replace(/"/g,`&quot;`).replace(/'/g,`&#39;`)}function q(e){return String(e||``).replace(/&/g,`&amp;`).replace(/</g,`&lt;`).replace(/>/g,`&gt;`).replace(/"/g,`&quot;`).replace(/'/g,`&#39;`)}function Te(e){return String(e||``).split(/\s+/).filter(Boolean).slice(0,2).map(e=>e[0]).join(``).toUpperCase()||`?`}function Ee(e,t){let n=document.createElement(`section`);n.className=`phase dash-v2 fade-in`,n.innerHTML=`
    <div class="dash-v2-container">
      <div class="wl-page-head">
        <div>
          <h2>Select Groups to Monitor</h2>
          <p data-subtitle>Loading your WhatsApp chats…</p>
        </div>
        <div class="wl-model-pill">
          <span class="material-symbols-outlined">group_work</span>
          Step 3 of 3
        </div>
      </div>

      <div class="wl-stats-row" data-stats-row>
        <div data-stats>Loading…</div>
      </div>

      <div class="wl-list" data-list>
        <div class="dash-v2-empty" data-loading>
          <span class="spinner"></span>
          <h3>Fetching chats…</h3>
          <p>Reading your WhatsApp conversations from the bridge.</p>
        </div>
      </div>

      <div class="wl-actionbar" data-actionbar>
        <div class="wl-actionbar-inner">
          <div class="wl-ab-count" data-selected-count>0</div>
          <div class="wl-ab-text">
            <strong>Groups Selected</strong>
            <span data-selected-breakdown>Select at least 1 group to proceed</span>
          </div>
          <button class="btn btn-primary" data-proceed disabled>
            Save & Discover Tasks
            <span class="material-symbols-outlined" style="font-size:18px">arrow_forward</span>
          </button>
        </div>
      </div>
    </div>
  `,e.appendChild(n);let r=e=>n.querySelector(e),i={subtitle:r(`[data-subtitle]`),stats:r(`[data-stats]`),list:r(`[data-list]`),loading:r(`[data-loading]`),selectedCount:r(`[data-selected-count]`),selectedBreakdown:r(`[data-selected-breakdown]`),proceedBtn:r(`[data-proceed]`)},a=new Set;function o(){let e=a.size;i.selectedCount.textContent=String(e),i.selectedCount.classList.toggle(`is-active`,e>0),i.proceedBtn.disabled=e<1,i.selectedBreakdown.textContent=e<1?`Select at least 1 group to proceed`:`${e} group${e===1?``:`s`} selected`}function s(e){let t=a.has(e.jid),n=document.createElement(`div`);return n.className=`wl-row`+(t?` is-selected`:``),n.dataset.jid=e.jid,n.innerHTML=`
      <div class="wl-avatar">${q(Te(e.name))}</div>
      <div class="wl-name">${q(e.name)}</div>
      <button class="wl-tick-btn" data-tick type="button">
        <span class="material-symbols-outlined">check</span>
      </button>
    `,n.addEventListener(`click`,e=>{e.target.closest(`[data-tick]`)||n.querySelector(`[data-tick]`).click()}),n.querySelector(`[data-tick]`).addEventListener(`click`,t=>{t.stopPropagation(),a.has(e.jid)?(a.delete(e.jid),n.classList.remove(`is-selected`)):(a.add(e.jid),n.classList.add(`is-selected`)),o()}),n}async function c(){i.loading.style.display=``,i.stats.textContent=`Loading…`;let e=[],t=0;for(;t<15;){let n=await N.getChats();if(!n.ok){i.list.innerHTML=`<div class="dash-v2-empty">
          <span class="material-symbols-outlined">error</span>
          <h3>Error</h3><p>${q(n.error||`Failed to fetch chats`)}</p>
          <button class="btn" onclick="location.reload()">Retry</button>
        </div>`;return}if(e=n.chats||[],e.length>0)break;i.subtitle.textContent=`Syncing WhatsApp messages…`,i.stats.textContent=`Syncing…`,i.list.innerHTML=`<div class="dash-v2-empty">
        <span class="spinner"></span>
        <h3>Syncing WhatsApp data\u2026</h3>
        <p>Importing your conversations. This may take a minute after first pairing.</p>
        <p style="font-size:12px;color:var(--on-surface-muted);margin-top:8px">Retry ${t+1}/15</p>
      </div>`,await new Promise(e=>setTimeout(e,3e3)),t++}if(e.length===0){i.list.innerHTML=`<div class="dash-v2-empty">
        <span class="material-symbols-outlined">chat</span>
        <h3>No chats found</h3>
        <p>Make sure your WhatsApp bridge is paired and has received messages.</p>
        <button class="btn" onclick="location.reload()">Retry</button>
      </div>`;return}i.stats.innerHTML=`<strong>${e.length}</strong> chats <span class="sep"></span> sorted by recent activity`,i.subtitle.textContent=`Select groups you want to monitor for tasks`;let n=document.createElement(`div`);n.className=`wl-rows`;for(let t of e)t.is_whitelisted&&a.add(t.jid),n.appendChild(s(t));i.loading.style.display=`none`,i.list.appendChild(n),o()}i.proceedBtn.addEventListener(`click`,async()=>{let e=[...a];if(e.length<1)return;i.proceedBtn.disabled=!0,i.proceedBtn.innerHTML=`<span class="spinner"></span> Saving…`;let t=await N.whitelistGroups(e);t.ok?Q(X.DASHBOARD,{autoDiscover:!0}):(i.proceedBtn.disabled=!1,i.proceedBtn.innerHTML=`Save & Discover Tasks <span class="material-symbols-outlined" style="font-size:18px">arrow_forward</span>`,i.selectedBreakdown.innerHTML=`<span style="color:var(--error)">Error: ${q(t.error||`Failed to save`)}</span>`)}),c()}var De={1:`⭐`,2:`⭐`,3:`⭐`,4:`⭐⭐`,5:`⭐⭐⭐`},Oe={1:`is-imp1`,2:`is-imp2`,3:`is-imp3`,4:`is-imp4`,5:`is-imp5`},ke={assignee:`Assignee`,requestor:`Requestor`,reviewer:`Reviewer`,stakeholder:`Stakeholder`},Ae={active:`is-active`,completed:`is-completed`,archived:`is-archived`};function J(e){return String(e||``).replace(/&/g,`&amp;`).replace(/</g,`&lt;`).replace(/>/g,`&gt;`).replace(/"/g,`&quot;`).replace(/'/g,`&#39;`)}function Y(e){if(!e)return`??`;let t=e.replace(/@.*$/,``),n=t.trim().split(/\s+/);return n.length>=2?(n[0][0]+n[n.length-1][0]).toUpperCase():t.substring(0,2).toUpperCase()}function je(e){if(!e)return``;try{let t=new Date(e);if(isNaN(t.getTime()))return``;let n=Date.now()-t.getTime(),r=Math.floor(n/6e4);if(r<1)return`just now`;if(r<60)return`${r}m ago`;let i=Math.floor(r/60);return i<24?`${i}h ago`:`${Math.floor(i/24)}d ago`}catch{return``}}function Me(e){if(!e)return``;try{return new Date(e).toLocaleDateString(`en-US`,{month:`short`,day:`numeric`})}catch{return``}}function Ne(e){if(!e)return``;try{let t=new Date(e),n=Math.floor((new Date-t)/864e5);return n===0?`Created today`:n===1?`Created yesterday`:n<7?`Created ${n}d ago`:`Created ${t.toLocaleDateString(`en-US`,{month:`short`,day:`numeric`})}`}catch{return``}}function Pe(e){if(!e)return``;try{let t=new Date(e);return t.toLocaleDateString(`en-US`,{month:`short`,day:`numeric`})+` · `+t.toLocaleTimeString(`en-US`,{hour:`2-digit`,minute:`2-digit`})}catch{return``}}function Fe(e,t){let n=document.createElement(`section`);n.className=`phase dash-v2 fade-in`,e.appendChild(n);let r=[],i=[],a=null,o=`all`,s=``;n.innerHTML=`
    <div class="dash-v2-container">
      <div class="dash-v2-stats" data-stats></div>
      <div class="dash-v2-search" data-search-row>
        <div class="dash-v2-search-input-wrap">
          <span class="material-symbols-outlined dash-v2-search-icon">search</span>
          <input class="dash-v2-search-input" placeholder="Search tasks…" data-search-input type="text" />
        </div>
      </div>
      <div class="dash-v2-filters" data-filters></div>
      <div class="dash-v2-progress" data-progress style="display:none"></div>
      <div data-task-area>
        <div class="dash-v2-empty"><span class="spinner"></span> Loading…</div>
      </div>
    </div>
  `;let c=e=>n.querySelector(e),l={stats:c(`[data-stats]`),searchInput:c(`[data-search-input]`),filters:c(`[data-filters]`),progress:c(`[data-progress]`),taskArea:c(`[data-task-area]`)};async function u(){let[e,n]=await Promise.all([N.getDashboard(),N.getGroupsV2()]);if(!e.ok){l.taskArea.innerHTML=`<div class="dash-v2-empty"><h3>Error</h3><p>${J(e.error||`Failed`)}</p></div>`;return}r=e.tasks||[],a=e.stats||null,i=n.ok&&n.groups?n.groups:[],d(),f(),m(),t.autoDiscover&&r.length===0&&i.length>0&&(t.autoDiscover=!1,await C(),await u())}function d(){if(!a)return;let e=[];e.push(`<strong>${a.total}</strong> tasks`),a.importance_5&&e.push(`<strong>${a.importance_5}</strong> critical`),a.completed&&e.push(`<strong>${a.completed}</strong> done`),a.last_refreshed&&e.push(`refreshed ${je(a.last_refreshed)}`),l.stats.innerHTML=e.map((t,n)=>`${t}${n<e.length-1?` <span class="sep"></span> `:``}`).join(``)+`<span style="margin-left:auto;display:flex;gap:8px">
          <button class="dash-v2-header-btn" data-action="discover"><span class="material-symbols-outlined">search</span> Discover</button>
          <button class="dash-v2-header-btn" data-action="refresh"><span class="material-symbols-outlined">refresh</span> Refresh</button>
        </span>`,l.stats.querySelector(`[data-action="discover"]`).addEventListener(`click`,C),l.stats.querySelector(`[data-action="refresh"]`).addEventListener(`click`,w)}function f(){let e=[{id:`all`,label:`All`},{id:`critical`,label:`Critical`},{id:`high`,label:`High`},null,{id:`active`,label:`Active`},null,{id:`work`,label:`Work`},{id:`personal`,label:`Personal`}];l.filters.innerHTML=e.map(e=>e?`<button class="dash-v2-filter-pill${o===e.id?` is-active`:``}" data-filter="${e.id}">${e.label}</button>`:`<span class="dash-v2-filter-sep"></span>`).join(``),l.filters.querySelectorAll(`[data-filter]`).forEach(e=>{e.addEventListener(`click`,()=>{o=e.dataset.filter,f(),m()})})}function p(){let e=[...r];if(o===`critical`&&(e=e.filter(e=>e.importance===5)),o===`high`&&(e=e.filter(e=>e.importance>=4)),o===`active`&&(e=e.filter(e=>e.status===`active`)),o===`work`){let t=i.filter(e=>e.category===`Work`).map(e=>e.jid);e=e.filter(e=>t.includes(e.group_jid))}if(o===`personal`){let t=i.filter(e=>e.category===`Personal`).map(e=>e.jid);e=e.filter(e=>t.includes(e.group_jid))}if(s.trim()){let t=s.toLowerCase();e=e.filter(e=>e.title.toLowerCase().includes(t)||(e.context||``).toLowerCase().includes(t)||(e.assignee||``).toLowerCase().includes(t)||(e.group_name||``).toLowerCase().includes(t))}return e}function m(){let e=p();if(r.length===0){l.taskArea.innerHTML=`<div class="dash-v2-empty">
        <span class="material-symbols-outlined">inbox</span>
        <h3>No tasks discovered yet</h3>
        <p>Click Discover Tasks to scan your WhatsApp chats for action items.</p>
        <button class="btn btn-primary" data-discover-cta><span class="material-symbols-outlined">search</span> Discover Tasks</button>
      </div>`,l.taskArea.querySelector(`[data-discover-cta]`).addEventListener(`click`,C);return}if(e.length===0){l.taskArea.innerHTML=`<div class="dash-v2-empty">
        <span class="material-symbols-outlined">filter_alt_off</span>
        <h3>No matching tasks</h3><p>Try another filter or search term.</p></div>`;return}let t=new Map;for(let n of e)t.has(n.group_jid)||t.set(n.group_jid,[]),t.get(n.group_jid).push(n);for(let[,e]of t)e.sort((e,t)=>e.status!==`active`&&t.status===`active`?1:e.status===`active`&&t.status!==`active`?-1:e.status===`archived`&&t.status===`completed`?1:e.status===`completed`&&t.status===`archived`?-1:(t.importance||0)-(e.importance||0));let n=[...t.entries()];n.sort((e,t)=>{let n=e[1].some(e=>e.importance===5);return n===t[1].some(e=>e.importance===5)?t[1].length-e[1].length:n?-1:1});let a=new Set(n.map(([e])=>e));for(let e of i)a.has(e.jid)||n.push([e.jid,[]]);let o=new Set,s=0;for(let[,e]of n)for(let t of e)t.importance===5&&t.status===`active`&&s<2&&(o.add(t.id),s++);let c=``;for(let[e,t]of n){let n=i.find(t=>t.jid===e),r=n?n.name:t[0]?.group_name||e,a=n?n.category:`Work`,s=t.length;if(c+=`<div class="dash-v2-group" data-group-jid="${J(e)}">`,c+=`<div class="dash-v2-group-head" data-group-toggle="${J(e)}">
        <span class="dash-v2-group-dot ${a===`Personal`?`is-personal`:`is-work`}"></span>
        <span class="dash-v2-group-name">${J(r)}</span>
        <span class="dash-v2-group-count">${s} ${s===1?`TASK`:`TASKS`}</span>
        <span class="material-symbols-outlined dash-v2-group-chevron" style="font-size:18px">expand_more</span>
      </div>`,t.length===0)c+=`<div class="dash-v2-group-empty">No active tasks. All clear!</div>`;else{c+=`<div class="dash-v2-tasks" data-group-body="${J(e)}">`;let n=0;for(let e of t){let t=e.importance===5,r=e.importance===4,i=Oe[e.importance]||`is-imp3`,a=je(e.updated_at||e.created_at),s=Me(e.created_at),l=Y(e.assignee),u=o.has(e.id),d=(t?` is-imp5`:r?` is-imp4`:e.importance===3?` is-imp3`:``)+(u?` is-top-priority`:``),f=e.status===`active`?`is-active`:e.status===`completed`?`is-completed`:`is-archived`;c+=`<div class="task-row${d}" data-task-id="${J(e.id)}">
            <div class="task-row-left">
              <div class="task-row-checkbox-wrap">
                <input type="checkbox" class="task-row-checkbox"
                  ${e.status===`completed`?`checked`:``}
                  ${e.status===`archived`?`disabled`:``}
                  data-checkbox-id="${J(e.id)}"
                />
              </div>
              <div class="task-row-title-wrap">
                <div class="task-row-title-line">
                  <span class="task-row-title${e.status===`active`?``:` is-`+e.status}">${J(e.title)}</span>
                  <span class="task-row-imp-tag ${i}">${De[e.importance]}</span>
                </div>
                <div class="task-row-meta">
                  <span class="task-row-meta-item">Updated ${a||`recently`}</span>
                  ${s?`<span class="task-row-meta-sep"></span><span class="task-row-meta-item">${Ne(e.created_at)}</span>`:``}
                </div>
              </div>
            </div>
            <div class="task-row-right">
              <div class="task-row-status">
                <span class="task-row-status-dot ${f}"></span>${e.status}
              </div>
              ${e.message_count>0?`<div class="task-row-msg-count"><span class="material-symbols-outlined">chat_bubble</span>${e.message_count}</div>`:``}
              <div class="task-row-avatar" title="${J(e.assignee)}">${l}</div>
              <button class="task-row-deep-dive" data-deep-dive="${J(e.id)}">
                ${e.has_deep_dive?`WIKI`:`DEEP DIVE`}
              </button>
            </div>
          </div>`,n++}c+=`</div>`}c+=`</div>`}l.taskArea.innerHTML=c,l.taskArea.querySelectorAll(`.task-row`).forEach(e=>{e.addEventListener(`click`,t=>{t.target.closest(`.task-row-deep-dive`)||t.target.closest(`.task-row-checkbox`)||g(e.dataset.taskId)})}),l.taskArea.querySelectorAll(`.task-row-checkbox`).forEach(e=>{e.addEventListener(`change`,async t=>{t.stopPropagation();let n=e.dataset.checkboxId,r=e.checked?`completed`:`active`,i=e.closest(`.task-row`);try{await N.updateTask(n,{status:r}),r===`completed`&&i?(i.classList.add(`is-completing`),i.addEventListener(`animationend`,()=>u(),{once:!0})):u()}catch{e.checked=!e.checked}})}),l.taskArea.querySelectorAll(`[data-deep-dive]`).forEach(e=>{e.addEventListener(`click`,t=>{t.stopPropagation(),g(e.dataset.deepDive)})}),l.taskArea.querySelectorAll(`[data-group-toggle]`).forEach(e=>{e.addEventListener(`click`,()=>{let t=e.dataset.groupToggle,n=l.taskArea.querySelector(`[data-group-body="${t}"]`),r=e.querySelector(`.dash-v2-group-chevron`);n&&(n.style.display=n.style.display===`none`?``:`none`,r&&r.classList.toggle(`is-open`,n.style.display!==`none`))})})}let h;l.searchInput.addEventListener(`input`,()=>{clearTimeout(h),h=setTimeout(()=>{s=l.searchInput.value,m()},200)}),document.addEventListener(`keydown`,e=>{(e.metaKey||e.ctrlKey)&&e.key===`k`&&(e.preventDefault(),l.searchInput.focus())});function g(e){let t=document.querySelector(`.task-modal-overlay`);t&&t.remove();let n=document.createElement(`div`);n.className=`task-modal-overlay`,n.innerHTML=`<div class="task-modal">
      <div class="task-modal-loading"><span class="spinner"></span><h3>Loading task…</h3></div>
    </div>`,document.body.appendChild(n),n.addEventListener(`click`,e=>{e.target===n&&_()}),v(e).then(({task:e,messages:t})=>y(n,e,t)).catch(e=>{let t=n.querySelector(`.task-modal`);t.innerHTML=`<div class="task-modal-loading"><h3>Error</h3><p>${J(e.message)}</p>
          <button class="btn" onclick="this.closest('.task-modal-overlay').remove()">Close</button></div>`})}function _(){let e=document.querySelector(`.task-modal-overlay`);e&&e.remove()}async function v(e){let[t,n]=await Promise.all([N.getTask(e),N.getTaskMessages(e)]);if(!t.ok)throw Error(t.error||`Task not found`);return{task:t.task,messages:n.ok&&n.messages?n.messages:[]}}function y(e,t,n){let r=Oe[t.importance]||`is-imp3`,i=t.people||[],a=t.progress_log||[],o=t.blockers||[],s=t.decisions||[],c=!!t.wiki,l=c||i.length>0||a.length>0,d=Y(t.assignee),f=Ae[t.status]||`is-active`,p=e.querySelector(`.task-modal`);p.innerHTML=`
      <div class="task-modal-head">
        <div class="task-modal-head-left">
          <span class="task-modal-imp-tag ${r}">${De[t.importance]}</span>
          <span class="task-modal-title">${J(t.title)}</span>
        </div>
        <div class="task-modal-head-right">
          <button class="task-modal-close" data-close><span class="material-symbols-outlined">close</span></button>
        </div>
      </div>
      <div class="task-modal-meta">
        <div class="task-modal-meta-group">
          <span class="task-modal-meta-label">ASSIGNEE</span>
          <div class="task-modal-meta-value">
            ${t.assignee?`<div class="task-row-avatar">${d}</div>`:``}
            <span>${J(t.assignee||`Unassigned`)}</span>
          </div>
        </div>
        <div class="task-modal-meta-sep"></div>
        <div class="task-modal-meta-group">
          <span class="task-modal-meta-label">STATUS</span>
          <div class="task-modal-meta-value">
            <span class="task-row-chip-dot ${f}"></span>
            <span>${t.status}</span>
          </div>
        </div>
        <div class="task-modal-meta-sep"></div>
        <div class="task-modal-meta-group">
          <span class="task-modal-meta-label">GROUP</span>
          <div class="task-modal-meta-value">
            <span class="material-symbols-outlined">groups</span>
            <span>${J(t.group_name||`Unknown`)}</span>
          </div>
        </div>
      </div>

      <div class="task-modal-body">
        ${t.context?`
          <div class="task-modal-overview">
            <div class="task-modal-overview-text">${J(t.context)}</div>
          </div>
        `:``}

        ${l?`
          ${c?`
            <div class="task-modal-collapse">
              <div class="task-modal-collapse-head" data-toggle="wiki">
                <div class="task-modal-collapse-head-left">
                  <span class="material-symbols-outlined" style="font-size:16px;color:var(--primary-container)">auto_awesome</span>
                  <span class="task-modal-collapse-label">Wiki (Deep-dive)</span>
                </div>
                <span class="material-symbols-outlined task-modal-collapse-chevron is-open" style="font-size:18px">expand_more</span>
              </div>
              <div class="task-modal-collapse-body" data-section="wiki">
                <div class="task-modal-wiki">${S(t.wiki)}</div>
              </div>
            </div>
          `:``}

          ${i.length>0?`
            <div class="task-modal-collapse">
              <div class="task-modal-collapse-head" data-toggle="people">
                <div class="task-modal-collapse-head-left">
                  <span class="material-symbols-outlined" style="font-size:16px;color:var(--on-surface-variant)">group</span>
                  <span class="task-modal-collapse-label">People</span>
                  <span class="task-modal-collapse-count">(${i.length})</span>
                </div>
                <span class="material-symbols-outlined task-modal-collapse-chevron is-open" style="font-size:18px">expand_more</span>
              </div>
              <div class="task-modal-collapse-body" data-section="people">
                <div class="task-modal-people">
                  ${i.map(e=>`
                    <div class="task-modal-person">
                      <div class="task-modal-person-left">
                        <div class="task-modal-person-avatar">${Y(e.name)}</div>
                        <span class="task-modal-person-name">${J(e.name||`Unknown`)}</span>
                      </div>
                      <span class="task-modal-person-role">${ke[e.role]||e.role||``}</span>
                    </div>
                  `).join(``)}
                </div>
              </div>
            </div>
          `:``}

          ${a.length>0?`
            <div class="task-modal-collapse">
              <div class="task-modal-collapse-head" data-toggle="timeline">
                <div class="task-modal-collapse-head-left">
                  <span class="material-symbols-outlined" style="font-size:16px;color:var(--on-surface-variant)">timeline</span>
                  <span class="task-modal-collapse-label">Timeline</span>
                  <span class="task-modal-collapse-count">(${a.length})</span>
                </div>
                <span class="material-symbols-outlined task-modal-collapse-chevron is-open" style="font-size:18px">expand_more</span>
              </div>
              <div class="task-modal-collapse-body" data-section="timeline">
                <div class="task-modal-timeline">
                  ${a.map((e,t)=>`
                    <div class="task-modal-tl-item">
                      <div class="task-modal-tl-dot${t===a.length-1?` is-active`:``}"></div>
                      <div class="task-modal-tl-date">${J(e.date||``)}</div>
                      <div class="task-modal-tl-text">${J(e.summary||``)}</div>
                    </div>
                  `).join(``)}
                </div>
              </div>
            </div>
          `:``}

          ${o.length>0?`
            <div class="task-modal-collapse">
              <div class="task-modal-collapse-head" data-toggle="blockers">
                <div class="task-modal-collapse-head-left">
                  <span class="material-symbols-outlined" style="font-size:16px;color:var(--st-pending)">block</span>
                  <span class="task-modal-collapse-label">Blockers</span>
                  <span class="task-modal-collapse-count">(${o.length})</span>
                </div>
                <span class="material-symbols-outlined task-modal-collapse-chevron is-open" style="font-size:18px">expand_more</span>
              </div>
              <div class="task-modal-collapse-body" data-section="blockers">
                ${o.map(e=>`
                  <div class="task-modal-info-card is-blocker" style="margin-bottom:8px">
                    <div class="task-modal-info-card-text">${J(e.description)}</div>
                    <div class="task-modal-info-card-meta">
                      <span>${J(e.raised_by||``)}</span>
                      <span>${J(e.date||``)}</span>
                    </div>
                  </div>
                `).join(``)}
              </div>
            </div>
          `:``}

          ${s.length>0?`
            <div class="task-modal-collapse">
              <div class="task-modal-collapse-head" data-toggle="decisions">
                <div class="task-modal-collapse-head-left">
                  <span class="material-symbols-outlined" style="font-size:16px;color:var(--on-surface-variant)">gavel</span>
                  <span class="task-modal-collapse-label">Decisions</span>
                  <span class="task-modal-collapse-count">(${s.length})</span>
                </div>
                <span class="material-symbols-outlined task-modal-collapse-chevron is-open" style="font-size:18px">expand_more</span>
              </div>
              <div class="task-modal-collapse-body" data-section="decisions">
                ${s.map(e=>`
                  <div class="task-modal-info-card" style="margin-bottom:8px">
                    <div class="task-modal-info-card-text">${J(e.description)}</div>
                    <div class="task-modal-info-card-meta">
                      <span>${J(e.made_by||``)}</span>
                      <span>${J(e.date||``)}</span>
                    </div>
                  </div>
                `).join(``)}
              </div>
            </div>
          `:``}

          ${n.length>0?`
            <div class="task-modal-collapse">
              <div class="task-modal-collapse-head" data-toggle="evidence">
                <div class="task-modal-collapse-head-left">
                  <span class="material-symbols-outlined" style="font-size:16px;color:var(--on-surface-variant)">chat</span>
                  <span class="task-modal-collapse-label">Evidence Trail</span>
                  <span class="task-modal-collapse-count">(${n.length})</span>
                </div>
                <span class="material-symbols-outlined task-modal-collapse-chevron" style="font-size:18px">expand_more</span>
              </div>
              <div class="task-modal-collapse-body is-hidden" data-section="evidence">
                ${n.map(e=>{let t=(e.sender_name||``).toLowerCase().includes(`you`);return`
                    <div class="evidence-item">
                      <div class="evidence-item-header">
                        <div class="evidence-avatar">${Y(e.sender_name||`?`)}</div>
                        <span class="evidence-sender">${J(e.sender_name||`Unknown`)}</span>
                        <span class="evidence-time">${Pe(e.message_time)}</span>
                      </div>
                      <div class="evidence-bubble ${t?`is-self`:`is-other`}">${J(e.message_content||``)}</div>
                    </div>
                  `}).join(``)}
              </div>
            </div>
          `:``}
        `:`
          <div class="task-modal-dd-placeholder">
            <span class="material-symbols-outlined">auto_awesome</span>
            <p>Run a deep-dive to generate a knowledge page with timeline, people, and decisions.</p>
            <button class="btn btn-primary" data-run-dd>
              <span class="material-symbols-outlined">analytics</span> Run Deep Dive
            </button>
          </div>
        `}

        ${n.length>0&&!l?`
          <div class="task-modal-collapse" style="margin-top:var(--s-md)">
            <div class="task-modal-collapse-head" data-toggle="evidence">
              <div class="task-modal-collapse-head-left">
                <span class="material-symbols-outlined" style="font-size:16px">chat</span>
                <span class="task-modal-collapse-label">Evidence Trail</span>
                <span class="task-modal-collapse-count">(${n.length})</span>
              </div>
              <span class="material-symbols-outlined task-modal-collapse-chevron is-open" style="font-size:18px">expand_more</span>
            </div>
            <div class="task-modal-collapse-body" data-section="evidence">
              ${n.map(e=>{let t=(e.sender_name||``).toLowerCase().includes(`you`);return`
                  <div class="evidence-item">
                    <div class="evidence-item-header">
                      <div class="evidence-avatar">${Y(e.sender_name||`?`)}</div>
                      <span class="evidence-sender">${J(e.sender_name||`Unknown`)}</span>
                      <span class="evidence-time">${Pe(e.message_time)}</span>
                    </div>
                    <div class="evidence-bubble ${t?`is-self`:`is-other`}">${J(e.message_content||``)}</div>
                  </div>
                `}).join(``)}
            </div>
          </div>
        `:``}

        <!-- Nudge Panel -->
        <div class="nudge-panel">
          <div class="nudge-panel-head">
            <span class="material-symbols-outlined">send</span> Send Nudge via WhatsApp
          </div>
          <div class="nudge-options" data-nudge-options>
            <div class="nudge-loading"><span class="spinner"></span> Generating nudge options\u2026</div>
          </div>
        </div>
      </div>

      <div class="task-modal-footer">
        <div class="task-modal-status-pills">
          <button class="task-modal-status-pill${t.status===`active`?` is-active`:``}" data-status="active">Active</button>
          <button class="task-modal-status-pill${t.status===`completed`?` is-active`:``}" data-status="completed">Completed</button>
          <button class="task-modal-status-pill${t.status===`archived`?` is-active`:``}" data-status="archived">Archived</button>
        </div>
        ${c?``:`<button class="btn btn-primary" data-modal-dd>Run Deep Dive</button>`}
      </div>
    `,p.querySelector(`[data-close]`).addEventListener(`click`,_),p.querySelectorAll(`[data-status]`).forEach(e=>{e.addEventListener(`click`,async()=>{let n=e.dataset.status;if(n!==t.status)if(await N.updateTask(t.id,{status:n}),_(),n===`completed`||n===`archived`){let e=document.querySelector(`.task-row[data-task-id="${t.id}"]`);e?(e.classList.add(`is-completing`),e.addEventListener(`animationend`,()=>u(),{once:!0})):u()}else u()})}),p.querySelector(`[data-modal-dd]`)?.addEventListener(`click`,()=>x(e,t.id)),p.querySelector(`[data-run-dd]`)?.addEventListener(`click`,()=>x(e,t.id)),p.querySelectorAll(`[data-toggle]`).forEach(e=>{e.addEventListener(`click`,()=>{let t=e.dataset.toggle,n=p.querySelector(`[data-section="${t}"]`),r=e.querySelector(`.task-modal-collapse-chevron`);n&&(n.classList.toggle(`is-hidden`),r&&r.classList.toggle(`is-open`,!n.classList.contains(`is-hidden`)))})}),b(t.id,p.querySelector(`[data-nudge-options]`))}async function b(e,t){try{let n=await N.generateNudges(e);if(!n.ok)throw Error(n.error||`Failed`);let r=n.nudges||[];t.innerHTML=r.map((e,t)=>`
        <div class="nudge-option" data-nudge-idx="${t}">
          <div class="nudge-option-head">
            <span class="nudge-option-tone ${e.tone===`gentle`?`is-gentle`:e.tone===`passive`?`is-passive`:`is-aggressive`}">${e.tone||`follow-up`}</span>
            <button class="nudge-option-send" data-send="${t}">
              <span class="material-symbols-outlined" style="font-size:14px">send</span> Send
            </button>
          </div>
          <div class="nudge-option-text">${J(e.text||``)}</div>
        </div>
      `).join(``),t.querySelectorAll(`[data-send]`).forEach(t=>{t.addEventListener(`click`,async n=>{n.stopPropagation();let i=r[parseInt(t.dataset.send)];if(i){t.disabled=!0,t.textContent=`Sending…`;try{(await N.sendNudge(e,i.text)).ok?(t.textContent=`Sent!`,t.style.color=`var(--tertiary)`,t.style.borderColor=`var(--tertiary)`):(t.textContent=`Failed`,t.style.color=`var(--error)`,t.style.borderColor=`var(--error)`)}catch{t.textContent=`Error`,t.style.color=`var(--error)`}setTimeout(()=>{t.disabled=!1},3e3)}})})}catch(e){t.innerHTML=`<div style="padding:var(--s-md);font-size:13px;color:var(--on-surface-muted)">
        Could not generate nudges. ${J(e.message)}</div>`}}async function x(e,t){let n=e.querySelector(`.task-modal`);n.innerHTML=`<div class="task-modal-loading">
      <span class="spinner"></span><h3>Running Deep Dive</h3>
      <p>Reading the full transcript and building a knowledge page. 5–20 seconds.</p>
    </div>`;try{let n=await N.deepDive(t);if(!n.ok)throw Error(n.error||`Deep-dive failed`);let[r]=await Promise.all([N.getTaskMessages(t)]),i=r.ok&&r.messages?r.messages:[];y(e,n.task,i)}catch(e){n.innerHTML=`<div class="task-modal-loading">
        <span class="material-symbols-outlined" style="font-size:36px;color:var(--error)">error</span>
        <h3>Deep-dive failed</h3><p>${J(e.message)}</p>
        <button class="btn" onclick="this.closest('.task-modal-overlay').remove()">Close</button>
      </div>`}}function S(e){if(!e)return``;let t=J(e);return t=t.replace(/^### (.+)$/gm,`<h4>$1</h4>`),t=t.replace(/^## (.+)$/gm,`<h3>$1</h3>`),t=t.replace(/^# (.+)$/gm,`<h2>$1</h2>`),t=t.replace(/\*\*(.+?)\*\*/g,`<strong>$1</strong>`),t=t.replace(/\*(.+?)\*/g,`<em>$1</em>`),t=t.replace(/^- (.+)$/gm,`<li>$1</li>`),t=t.replace(/(<li>.*<\/li>)/s,`<ul>$1</ul>`),t=t.split(/\n\n+/).map(e=>e.startsWith(`<h`)||e.startsWith(`<ul`)?e:`<p>${e.replace(/\n/g,`<br>`)}</p>`).join(`
`),t}async function C(){if(i.length===0){l.progress.style.display=``,l.progress.innerHTML=`<div class="dash-v2-progress-inner dash-v2-progress-error">No groups whitelisted.</div>`;return}l.progress.style.display=``,l.progress.innerHTML=`<div class="dash-v2-progress-inner">
      <div class="dash-v2-progress-head"><span class="spinner"></span> Discovering tasks across ${i.length} groups\u2026</div>
      <div data-stream-list></div></div>`;let e=l.progress.querySelector(`[data-stream-list]`);await N.discoverTasksStream({jids:i.map(e=>e.jid),onMeta:e=>{l.progress.querySelector(`.dash-v2-progress-head`).innerHTML=`<span class="spinner"></span> Discovering across ${e.total} groups\u2026`},onGroup:t=>{let n=t.status===`ok`?`dash-v2-progress-ok`:t.status===`no_messages`?`dash-v2-progress-warn`:`dash-v2-progress-error`;e.innerHTML+=`<div class="dash-v2-progress-item ${n}"><span class="material-symbols-outlined">${t.status===`ok`?`check_circle`:`error`}</span> ${J(t.name)} — ${t.task_count} tasks</div>`},onDone:e=>{l.progress.innerHTML=`<div class="dash-v2-progress-inner"><div class="dash-v2-progress-done"><span class="material-symbols-outlined">check_circle</span> Discovery: ${e.total_tasks_found} tasks in ${e.groups_with_tasks} groups.</div></div>`,setTimeout(()=>{l.progress.style.display=`none`},5e3),u()},onError:e=>{l.progress.innerHTML=`<div class="dash-v2-progress-inner dash-v2-progress-error">Error: ${J(e.error)}</div>`}})}async function w(){if(i.length===0)return;l.progress.style.display=``,l.progress.innerHTML=`<div class="dash-v2-progress-inner">
      <div class="dash-v2-progress-head"><span class="spinner"></span> Refreshing tasks…</div>
      <div data-stream-list></div></div>`;let e=l.progress.querySelector(`[data-stream-list]`);await N.refreshTasksStream({jids:i.map(e=>e.jid),onMeta:e=>{l.progress.querySelector(`.dash-v2-progress-head`).innerHTML=`<span class="spinner"></span> Refreshing ${e.total_known_tasks} tasks\u2026`},onTask:t=>{e.innerHTML+=`<div class="dash-v2-progress-item dash-v2-progress-ok"><span class="material-symbols-outlined">update</span> ${J(t.progress_note||t.status_update)}</div>`},onNewTask:t=>{e.innerHTML+=`<div class="dash-v2-progress-item dash-v2-progress-ok"><span class="material-symbols-outlined">add_circle</span> New: ${J(t.title)}</div>`},onDone:e=>{l.progress.innerHTML=`<div class="dash-v2-progress-inner"><div class="dash-v2-progress-done"><span class="material-symbols-outlined">check_circle</span> Refresh: ${e.updated} updated, ${e.completed} done, ${e.new} new.</div></div>`,setTimeout(()=>{l.progress.style.display=`none`},5e3),u()},onError:e=>{l.progress.innerHTML=`<div class="dash-v2-progress-inner dash-v2-progress-error">Error: ${J(e.error)}</div>`}})}u()}var X={APIKEY:`apikey`,PAIRING:`pairing`,WHITELIST:`whitelist`,CLASSIFY:`classify`,EXTRACT:`extract`,KANBAN:`kanban`,DASHBOARD:`dashboard`},Z={phase:X.APIKEY,selectedChats:[],activeCategory:`all`,lastSynced:null,error:null,health:null};function Ie(){return Z}function Q(e,t={}){Z.phase=e,Object.assign(Z,t),$()}function Le(e){e.innerHTML=``;let t=document.createElement(`div`);t.className=`app-shell`,e.appendChild(t);let n=document.createElement(`div`);n.className=`app-main`,t.appendChild(n),Z.phase!==X.PAIRING&&Z.phase!==X.APIKEY&&xe(n,Z);let r=document.createElement(`main`);return r.className=`main`,n.appendChild(r),r}function Re(e){if(!e)return`Last Synced: just now`;try{let t=new Date(e);if(isNaN(t.getTime()))return`Last Synced: just now`;let n=Date.now()-t.getTime(),r=Math.floor(n/6e4);if(r<1)return`Last Synced: just now`;if(r<60)return`Last Synced: ${r} min ago`;let i=Math.floor(r/60);return i<24?`Last Synced: ${i} hr ago`:`Last Synced: ${t.toLocaleDateString()}`}catch{return`Last Synced: just now`}}function $(){let e=document.getElementById(`app`);if(!e)return;let t=Le(e);switch(Z.phase){case X.APIKEY:Ce(t,Z);break;case X.PAIRING:se(t,Z);break;case X.WHITELIST:Ee(t,Z);break;case X.CLASSIFY:le(t,Z);break;case X.EXTRACT:ue(t,Z);break;case X.KANBAN:ye(t,Z);break;case X.DASHBOARD:Fe(t,Z);break}}function ze(e){console.log(`[app] renderApp() — calling healthV2()`),N.healthV2().then(e=>{console.log(`[app] health response:`,e),Z.health=e,e.gemini_key_set?e.bridge_status===`connected`?N.getGroupsV2().then(e=>{e.ok&&e.groups&&e.groups.length>0?Z.phase=X.DASHBOARD:Z.phase=X.WHITELIST,$()}).catch(()=>{Z.phase=X.WHITELIST,$()}):(console.log(`[app] bridge_status=${e.bridge_status} → PAIRING phase`),Z.phase=X.PAIRING):(console.log(`[app] no key set → APIKEY phase`),Z.phase=X.APIKEY),$()}).catch(()=>{Z.phase=X.APIKEY,$()}),N.bridgeStatus().then(e=>{if(e&&e.connected_at){Z.lastSynced=e.connected_at;let t=document.querySelector(`[data-sync-label]`);t&&(t.textContent=Re(e.connected_at))}}).catch(()=>{})}ze(document.getElementById(`app`));
//# sourceMappingURL=index-CxLkjeJC.js.map