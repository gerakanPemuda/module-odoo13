export default function (props, ctx) {
  var $f7router = ctx.$f7router;
  var $el = ctx.$el;
  var $f7 = ctx.$f7;
  var $onMounted = ctx.$onMounted;
  var $on = ctx.$on;

  function onResize() {
    if ($f7.width >= 768) {
      $el.value.find('.list:not(.searchbar-not-found)').addClass('menu-list');
    } else {
      $el.value.find('.list:not(.searchbar-not-found)').removeClass('menu-list');
    }
  }

  if ($f7.theme === 'aurora') {
    $onMounted(function () {
      $el.value.find('.list a[href]:not(.external)').attr('data-reload-detail', 'true');
      onResize();
    });

    $on('pageAfterIn', function () {
      if ($f7.width >= 768) {
        $f7router.navigate('/about/', { reloadDetail: true });
      }
    })

    $f7.on('resize', onResize);

    $f7router.on('routeChange', function (route) {
      var url = route.url;
      if (!$el.value) return;
      var $linkEl = $el.value.find('a[href="' + url + '"]');
      if (!$linkEl.length) return;
      $el.value.find('.item-selected').removeClass('item-selected');
      $linkEl.addClass('item-selected');
    });
  }

  return $render;
};