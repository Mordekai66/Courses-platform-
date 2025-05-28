const headers = document.querySelectorAll('.accordion-header');

headers.forEach(header => {
  header.addEventListener('click', () => {
    header.classList.toggle('active');
    const content = header.nextElementSibling;
    content.classList.toggle('open');
  });
});

const darkModeBtn = document.getElementById('darkModeToggle');
const icon = darkModeBtn.querySelector('.icon');

darkModeBtn.addEventListener('click', () => {
  document.body.classList.toggle('dark-mode');

  // أضف حركة دوران خفيفة للزر نفسه وقت التبديل
  darkModeBtn.classList.add('clicked');
  setTimeout(() => {
    darkModeBtn.classList.remove('clicked');
  }, 300);

  if (document.body.classList.contains('dark-mode')) {
    icon.textContent = '☀️';
  } else {
    icon.textContent = '🌙';
  }
});
