<template>
  <div>
    <div class="container mt-5">
      <div class="text-center mb-4">
        <img src="/public/bball.png" alt="Basketball" class="header-icon" />
        <h1 class="d-inline mx-3">MADNESS.IO</h1>
        <img src="/public/bball.png" alt="Basketball" class="header-icon" />
      </div>
    </div>

    <RouterView />

    <div class="container">
      <footer class="text-center mt-5 text-muted">Contact: timthemoran@gmail.com</footer>
    </div>
  </div>
</template>

<style scoped>
.header-icon {
  height: 50px;
  width: 50px;
  margin-top: -22px;
}
</style>
