<?php

/**
* @package   s9e\TextFormatter
* @copyright Copyright (c) 2010-2023 The s9e authors
* @license   http://www.opensource.org/licenses/mit-license.php The MIT License
*/
class Renderer_3539886cc57888c5c0db03086fa5468eee8df737 extends \s9e\TextFormatter\Renderers\PHP
{
	protected $params=[];
	protected function renderNode(\DOMNode $node)
	{
		switch($node->nodeName){case'EMAIL':$this->out.='<a href="mailto:'.htmlspecialchars($node->getAttribute('email'),2).'">';$this->at($node);$this->out.='</a>';break;case'ESC':$this->at($node);break;case'URL':$this->out.='<a href="'.htmlspecialchars($node->getAttribute('url'),2).'"';if($node->hasAttribute('rel'))$this->out.=' rel="'.htmlspecialchars($node->getAttribute('rel'),2).'"';if($node->hasAttribute('target'))$this->out.=' target="'.htmlspecialchars($node->getAttribute('target'),2).'"';$this->out.='>';$this->at($node);$this->out.='</a>';break;case'br':$this->out.='<br>';break;case'e':case'i':case's':break;case'p':$this->out.='<p>';$this->at($node);$this->out.='</p>';break;default:$this->at($node);}
	}
	/** {@inheritdoc} */
	public $enableQuickRenderer=true;
	/** {@inheritdoc} */
	protected $static=['/EMAIL'=>'</a>','/ESC'=>'','/URL'=>'</a>','ESC'=>''];
	/** {@inheritdoc} */
	protected $dynamic=['EMAIL'=>['(^[^ ]+(?> (?!email=)[^=]+="[^"]*")*(?> email="([^"]*)")?.*)s','<a href="mailto:$1">'],'URL'=>['(^[^ ]+(?> (?!(?:rel|target|url)=)[^=]+="[^"]*")*( rel="[^"]*")?(?> (?!(?:target|url)=)[^=]+="[^"]*")*( target="[^"]*")?(?> (?!url=)[^=]+="[^"]*")*(?> url="([^"]*)")?.*)s','<a href="$3"$1$2>']];
	/** {@inheritdoc} */
	protected $quickRegexp='(<(?:(?!/)((?!))(?: [^>]*)?>.*?</\\1|(/?(?!br/|p>)[^ />]+)[^>]*?(/)?)>)s';
	/** {@inheritdoc} */
	protected function renderQuickTemplate($id, $xml)
	{
		$attributes=$this->matchAttributes($xml);
		$html='';

		return $html;
	}
}