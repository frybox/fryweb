from fryhcs import Element

def RefApp(props):
    return (
    <div>
      <p ref=(foo)>
        Hello World!
      </p>
    </div>
    <script foo bar>
      setTimeout(()=>{
        foo.style.transform = "skewY(180deg)";
      }, 1000);
      setTimeout(()=>{
        bar.style.transform = "skewY(180deg)";
      }, 2000);
    </script>)

if __name__ == '__main__':
    from fryhcs import render
    print(render(RefApp))