
<style>
.hr-solid-content{
    color: #a2a9b6;
    border: 0;
    font-size: 12px;
    padding: 1em 0;
    position: relative;
}
.hr-solid-content::before {
    content: attr(data-content);
    position: absolute;
    padding: 0 1ch;
    line-height: 1px;
    border: solid #d0d0d5;
    border-width: 0 99vw;
    width: fit-content;
    /* for IE浏览器 */
    white-space: nowrap;
    left: 50%;
    transform: translateX(-50%);
}
  .hr-solid-content::after{
    content: attr(data-content);
    position: absolute;
    padding: 4px 1ch;
    top: 50%; left: 50%;
    transform: translate(-50%, -50%);
    color: transparent;
    border: 1px solid #d0d0d5;
    
}
</style>

<hr class="hr-solid-content" data-content="Sea" width="420" align="left">
<br>

<img src="https://raw.githubusercontent.com/OrekiYuta/OrekiYuta/main/OrekiYuta.png"  height="515" width="300" align="right">

- A white bird drifting alone.

- Blending neither into the blue of the sky nor the blue of the sea.

- Flying on the white wings to the tropical island between the two blue worlds.

<hr class="hr-solid-content" data-content="Sky">
<br>

- We've always fooled around together since we were kids.

- We've shared the most exciting moments, but every story has an end.

- No one can stay a kid forever.

- Time moves on, and people grow up.

- We must go our separate ways.

- You must keep going even after I'm gone.

