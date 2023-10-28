from fryhcs import Element

def RefApp(**props):
    return (
    <div>
      <p ref=(foo)>
        Hello World!
      </p>
      <p ref=(foo)>
        Hello FryHCS!
      </p>
    </div>
    <script foo>
      setTimeout(()=>{
        foo.style.transform = "skewY(180deg)";
      }, 1000);
    </script>)

if __name__ == '__main__':
    from fryhcs import render
    print(render(RefApp))
