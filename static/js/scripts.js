// const smallCups = document.querySelectorAll('.cup-small')
// const liters =  document.getElementById('liters')
// const percentage =document.getElementById('percentage')
// const remained = document.getElementById('remained')
// const remain_water = []
// const remain_percentage=[]
// updateBigCup()
// smallCups.forEach((cup,idx) =>{
//     cup.addEventListener('click', ()=>highlightCups(idx))
// })

// function highlightCups(idx){
//     if (idx ===7 && smallCups[idx].classList.contains("full")) idx--;
//     else if (smallCups[idx].classList.contains('full') && !smallCups[idx].nextElementSibling.classList.contains('full')){
//         idx--
//     }

//     smallCups.forEach((cup,idx2)=>{
//         if (idx2<=idx){
//             cup.classList.add('full')
//         }
//         else{
//             cup.classList.remove('full')
//         }
//     })

//     updateBigCup()
// }

// function updateBigCup(){
//     const fullCups=document.querySelectorAll('.cup-small.full').length
//     const totalCups=smallCups.length

//     if(fullCups === 0){
//         percentage.style.visibility='hidden'
//         percentage.style.height=0
//     }
//     else{
//         percentage.style.visibility='visible'
//         percentage.style.height=`${fullCups/totalCups * 330}px`
//         percentage.innerText=`${fullCups/totalCups*100}%`
//         remain_percentage.push(percentage)
//         console.log(remain_percentage[remain_percentage.length -1])

//     }


//     if (fullCups===totalCups){
//         remained.style.visibility="hidden"
//         remained.style.height=0
//     }
//     else{
//         remained.style.visibility='visible'
//         liters.innerText=`${2-(250 * fullCups/1000)}L`
//         remain_water.push(liters)
//         console.log(remain_water[remain_water.length -1])
//     }
// }



const smallCups = document.querySelectorAll('.cup-small');
const liters = document.getElementById('liters');
const percentage = document.getElementById('percentage');
const remained = document.getElementById('remained');

// Load saved data from localStorage on page load
document.addEventListener('DOMContentLoaded', () => {
    const savedCups = localStorage.getItem('fullCups');
    if (savedCups) {
        const fullCups = JSON.parse(savedCups);
        fullCups.forEach(idx => smallCups[idx].classList.add('full'));
        updateBigCup();
    }
});

// Add event listeners to cups
smallCups.forEach((cup, idx) => {
    cup.addEventListener('click', () => highlightCups(idx));
});

function highlightCups(idx) {
    if (idx === 7 && smallCups[idx].classList.contains('full')) idx--;
    else if (
        smallCups[idx].classList.contains('full') &&
        !smallCups[idx].nextElementSibling.classList.contains('full')
    ) {
        idx--;
    }

    smallCups.forEach((cup, idx2) => {
        if (idx2 <= idx) {
            cup.classList.add('full');
        } else {
            cup.classList.remove('full');
        }
    });

    updateBigCup();
    saveProgress(); // Save progress after every update
}

function updateBigCup() {
    const fullCups = document.querySelectorAll('.cup-small.full').length;
    const totalCups = smallCups.length;

    if (fullCups === 0) {
        percentage.style.visibility = 'hidden';
        percentage.style.height = 0;
    } else {
        percentage.style.visibility = 'visible';
        percentage.style.height = `${(fullCups / totalCups) * 330}px`;
        percentage.innerText = `${(fullCups / totalCups) * 100}%`;
    }

    if (fullCups === totalCups) {
        remained.style.visibility = 'hidden';
        remained.style.height = 0;
    } else {
        remained.style.visibility = 'visible';
        liters.innerText = `${2 - (250 * fullCups) / 1000}L`;
    }
}

// Save progress to localStorage
function saveProgress() {
    const fullCups = [];
    smallCups.forEach((cup, idx) => {
        if (cup.classList.contains('full')) {
            fullCups.push(idx);
        }
    });
    localStorage.setItem('fullCups', JSON.stringify(fullCups));
}
